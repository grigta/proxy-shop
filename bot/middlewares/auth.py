"""Authentication middleware for bot."""
from typing import Callable, Dict, Any, Awaitable, Optional
from aiogram import BaseMiddleware
from aiogram.types import Update, User as TelegramUser

from bot.services.api_client import BackendAPIClient
from bot.core.config import bot_settings
from bot.core.logging_config import get_logger

logger = get_logger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Middleware to handle user authentication and inject API client."""
    
    def __init__(self):
        """Initialize auth middleware."""
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        """Process update and inject authenticated API client.
        
        Args:
            handler: Next handler in chain
            event: Incoming update
            data: Handler data dictionary
            
        Returns:
            Handler result
        """
        # Get Telegram user from event
        telegram_user: Optional[TelegramUser] = data.get("event_from_user")
        
        if not telegram_user:
            # No user in update, skip auth
            return await handler(event, data)
        
        # Get FSM context to store/retrieve tokens
        state = data.get("state")
        if not state:
            logger.warning("No FSM state available for auth")
            return await handler(event, data)
        
        # Extract access_code and referral_code from deep-link BEFORE reading FSM state
        access_code_from_deeplink: Optional[str] = None
        referral_code_from_deeplink: Optional[str] = None
        
        if event.message and event.message.text:
            message_text = event.message.text
            if message_text.startswith("/start"):
                parts = message_text.split(maxsplit=1)
                if len(parts) > 1:
                    arg = parts[1]
                    # Check if it's an access_code (format: XXX-XXX-XXX)
                    if "-" in arg and len(arg) == 11:
                        access_code_from_deeplink = arg
                        logger.info(f"Access code from deep-link: {access_code_from_deeplink}")
                    else:
                        # Otherwise it's a referral code
                        referral_code_from_deeplink = arg
                        logger.info(f"Referral code from deep-link: {referral_code_from_deeplink}")
        
        # Create API client
        api_client = BackendAPIClient()
        
        try:
            # Try to get tokens from FSM storage
            state_data = await state.get_data()
            access_token = state_data.get("access_token")
            refresh_token = state_data.get("refresh_token")
            
            # Priority 1: Try to login with access_code from deep-link
            if access_code_from_deeplink and not access_token:
                try:
                    login_response = await api_client.login_by_access_code(access_code_from_deeplink)
                    access_token = login_response["access_token"]
                    refresh_token = login_response.get("refresh_token")
                    
                    # Save access_code to state
                    await state.update_data(
                        access_token=access_token,
                        refresh_token=refresh_token,
                        access_code=access_code_from_deeplink
                    )
                    
                    api_client.set_access_token(access_token, refresh_token)
                    logger.info(f"User {telegram_user.id} logged in via access_code")
                except Exception as e:
                    logger.warning(f"Failed to login with access_code: {e}")
                    access_token = None
            
            # Priority 2: Validate existing token
            if access_token:
                # Set tokens in API client
                api_client.set_access_token(access_token, refresh_token)
                
                # Try to get user profile to verify token
                try:
                    user_profile = await api_client.get_user_profile()
                    data["user_profile"] = user_profile
                    data["is_authenticated"] = True
                    logger.debug(f"User {telegram_user.id} authenticated")
                
                except Exception as e:
                    logger.info(f"Token validation failed for user {telegram_user.id}: {e}")
                    # Token invalid, need to re-authenticate
                    access_token = None
            
            # Priority 3: Register new Telegram user OR get existing user
            if not access_token:
                # Clear old invalid tokens from state before re-authenticating
                await state.update_data(
                    access_token=None,
                    refresh_token=None
                )
                
                try:
                    language = telegram_user.language_code or "ru"
                    if language not in ["ru", "en"]:
                        language = "ru"
                    
                    # Use referral_code from deep-link or from previously saved state
                    referral_code = referral_code_from_deeplink or state_data.get("referral_code")
                    
                    # Save referral code to state for future use
                    if referral_code:
                        await state.update_data(referral_code=referral_code)
                    
                    # Use unified Telegram authentication endpoint
                    auth_response = await api_client.authenticate_telegram(
                        telegram_id=telegram_user.id,
                        username=telegram_user.username,
                        language=language,
                        referral_code=referral_code
                    )
                    
                    access_token = auth_response["access_token"]
                    refresh_token = auth_response.get("refresh_token")
                    access_code = auth_response.get("access_code")
                    is_new_user = auth_response.get("is_new_user", False)
                    
                    logger.info(f"User {telegram_user.id} authenticated (new={is_new_user}) with access_code {access_code}")
                    
                    # Set tokens
                    api_client.set_access_token(access_token, refresh_token)
                    
                    # Save tokens and access_code to FSM storage
                    await state.update_data(
                        access_token=access_token,
                        refresh_token=refresh_token,
                        access_code=access_code
                    )
                    
                    # Get user profile
                    user_profile = await api_client.get_user_profile()
                    data["user_profile"] = user_profile
                    data["is_authenticated"] = True
                
                except Exception as e:
                    logger.error(f"Authentication failed for user {telegram_user.id}: {e}")
                    # Clear all auth data from state on authentication failure
                    await state.update_data(
                        access_token=None,
                        refresh_token=None,
                        access_code=None
                    )
                    data["is_authenticated"] = False
            
            # Inject API client into handler data
            data["api_client"] = api_client
            
            # Call next handler
            result = await handler(event, data)
            
            return result
        
        finally:
            # Don't close client here as it may be used in handlers
            # Handlers should close it if needed, or it will be closed on bot shutdown
            pass
