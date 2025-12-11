/**
 * Copy text to clipboard with fallback for non-HTTPS contexts
 *
 * Modern browsers require HTTPS for navigator.clipboard.writeText()
 * This function provides a fallback using document.execCommand for HTTP contexts
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  // Try modern clipboard API first (works in HTTPS)
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      console.warn('Clipboard API failed, trying fallback method', err);
    }
  }

  // Fallback for HTTP contexts or older browsers
  try {
    // Create a temporary textarea element
    const textarea = document.createElement('textarea');
    textarea.value = text;

    // Make it invisible but still in the DOM
    textarea.style.position = 'fixed';
    textarea.style.top = '-9999px';
    textarea.style.left = '-9999px';
    textarea.setAttribute('readonly', '');

    document.body.appendChild(textarea);

    // Select the text
    textarea.select();
    textarea.setSelectionRange(0, text.length);

    // Copy using execCommand
    const successful = document.execCommand('copy');

    // Clean up
    document.body.removeChild(textarea);

    return successful;
  } catch (err) {
    console.error('Failed to copy text to clipboard:', err);
    return false;
  }
}
