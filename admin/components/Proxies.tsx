import React, { useState, useEffect } from 'react';
import { Search, Upload, Trash2, ChevronDown, ChevronRight, Edit2 } from 'lucide-react';
import { Language } from '../types';
import { TRANSLATIONS } from '../constants';
import { adminApiClient } from '../lib/api-client';

interface ProxiesProps {
  lang: Language;
}

interface PptpProxy {
  product_id: number;
  ip: string;
  login: string;
  password: string;
  country: string;
  state: string;
  city: string;
  zip: string;
  created_at: string;
}

interface Catalog {
  id: number;
  name: string;
  price: string;
  count?: number;
  proxies?: PptpProxy[];
  isExpanded?: boolean;
  isLoading?: boolean;
}

const Proxies: React.FC<ProxiesProps> = ({ lang }) => {
  const t = TRANSLATIONS[lang];
  const [catalogs, setCatalogs] = useState<Catalog[]>([]);
  const [isBulkModalOpen, setIsBulkModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [isDeleting, setIsDeleting] = useState(false);

  // Bulk upload state
  const [bulkData, setBulkData] = useState('');
  const [bulkFormat, setBulkFormat] = useState('line');

  // Catalog selection for upload
  const [catalogsForSelect, setCatalogsForSelect] = useState<Array<{ id: number; name: string; price: string }>>([]);
  const [selectedCatalogId, setSelectedCatalogId] = useState<number | null>(null);
  const [isCreatingNewCatalog, setIsCreatingNewCatalog] = useState(false);
  const [newCatalogName, setNewCatalogName] = useState('');
  const [newCatalogPrice, setNewCatalogPrice] = useState('');

  // Catalog editing state
  const [editingCatalog, setEditingCatalog] = useState<Catalog | null>(null);
  const [editName, setEditName] = useState('');
  const [editPrice, setEditPrice] = useState('');
  const [editDescRu, setEditDescRu] = useState('');
  const [editDescEn, setEditDescEn] = useState('');
  const [isUpdatingCatalog, setIsUpdatingCatalog] = useState(false);

  // Fetch catalogs from API
  useEffect(() => {
    fetchCatalogs();
  }, []);

  const fetchCatalogs = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await adminApiClient.getCatalogs('PPTP');
      const catalogsData = response.catalogs || [];

      // Get count for each catalog
      const catalogsWithCount = await Promise.all(
        catalogsData.map(async (catalog: { id: number; name: string; price: string }) => {
          try {
            const proxiesResponse = await adminApiClient.getPptpProxies(1, 1, undefined, catalog.id);
            return {
              ...catalog,
              count: proxiesResponse.total || 0,
              isExpanded: false,
              isLoading: false,
              proxies: []
            };
          } catch (err) {
            return {
              ...catalog,
              count: 0,
              isExpanded: false,
              isLoading: false,
              proxies: []
            };
          }
        })
      );

      setCatalogs(catalogsWithCount);
    } catch (err: any) {
      console.error('Error fetching catalogs:', err);
      setError(err.response?.data?.detail || 'Failed to load catalogs');
    } finally {
      setLoading(false);
    }
  };

  const fetchCatalogsForSelect = async () => {
    try {
      const response = await adminApiClient.getCatalogs('PPTP');
      setCatalogsForSelect(response.catalogs || []);
    } catch (err: any) {
      console.error('Error fetching catalogs for select:', err);
    }
  };

  const openEditCatalog = (catalog: Catalog, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent catalog expand/collapse
    setEditingCatalog(catalog);
    setEditName(catalog.name);
    setEditPrice(catalog.price);
    setEditDescRu('');
    setEditDescEn('');
  };

  const handleUpdateCatalog = async () => {
    if (!editingCatalog) return;

    setIsUpdatingCatalog(true);
    try {
      await adminApiClient.updateCatalog(editingCatalog.id, {
        line_name: editName,
        price: parseFloat(editPrice),
        description_ru: editDescRu || undefined,
        description_eng: editDescEn || undefined,
      });

      // Update local state
      setCatalogs(catalogs.map(c =>
        c.id === editingCatalog.id
          ? { ...c, name: editName, price: editPrice }
          : c
      ));

      setEditingCatalog(null);
      alert('Catalog updated successfully');
    } catch (err: any) {
      console.error('Error updating catalog:', err);
      alert(err.response?.data?.detail || 'Failed to update catalog');
    } finally {
      setIsUpdatingCatalog(false);
    }
  };

  const handleDeleteCatalog = async (catalogId: number, catalogName: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!confirm(`Are you sure you want to delete catalog "${catalogName}" and all its proxies? This action cannot be undone.`)) {
      return;
    }

    try {
      await adminApiClient.deleteCatalog(catalogId);
      setCatalogs(catalogs.filter(c => c.id !== catalogId));
      alert('Catalog deleted successfully');
    } catch (err: any) {
      console.error('Error deleting catalog:', err);
      alert(err.response?.data?.detail || 'Failed to delete catalog');
    }
  };

  const toggleCatalog = async (catalogId: number) => {
    const catalog = catalogs.find(c => c.id === catalogId);
    if (!catalog) return;

    // If already expanded, just collapse
    if (catalog.isExpanded) {
      setCatalogs(catalogs.map(c =>
        c.id === catalogId ? { ...c, isExpanded: false } : c
      ));
      return;
    }

    // If not expanded and no proxies loaded yet, fetch them
    if (!catalog.proxies || catalog.proxies.length === 0) {
      setCatalogs(catalogs.map(c =>
        c.id === catalogId ? { ...c, isLoading: true } : c
      ));

      try {
        const response = await adminApiClient.getPptpProxies(1, 1000, undefined, catalogId);
        setCatalogs(catalogs.map(c =>
          c.id === catalogId
            ? { ...c, proxies: response.proxies || [], isExpanded: true, isLoading: false }
            : c
        ));
      } catch (err: any) {
        console.error('Error fetching proxies for catalog:', err);
        setCatalogs(catalogs.map(c =>
          c.id === catalogId ? { ...c, isLoading: false } : c
        ));
      }
    } else {
      // Just expand with existing data
      setCatalogs(catalogs.map(c =>
        c.id === catalogId ? { ...c, isExpanded: true } : c
      ));
    }
  };

  const handleBulkUpload = async () => {
    if (!bulkData.trim()) {
      alert('Please enter proxy data');
      return;
    }

    // Validate catalog selection
    if (isCreatingNewCatalog) {
      if (!newCatalogName.trim()) {
        alert('Please enter catalog name');
        return;
      }
      if (!newCatalogPrice.trim() || isNaN(parseFloat(newCatalogPrice))) {
        alert('Please enter valid catalog price');
        return;
      }
    }

    try {
      const catalogId = isCreatingNewCatalog ? undefined : (selectedCatalogId || undefined);
      const catalogName = isCreatingNewCatalog ? newCatalogName : undefined;
      const catalogPrice = isCreatingNewCatalog ? parseFloat(newCatalogPrice) : undefined;

      const result = await adminApiClient.bulkUploadPPTP(
        bulkData,
        bulkFormat,
        catalogId,
        catalogName,
        catalogPrice
      );

      alert(`✅ Successfully created ${result.created_count} PPTP proxies${result.failed_count > 0 ? ` (${result.failed_count} errors)` : ''}`);

      setIsBulkModalOpen(false);
      setBulkData('');
      setIsCreatingNewCatalog(false);
      setNewCatalogName('');
      setNewCatalogPrice('');
      setSelectedCatalogId(null);

      // Refresh list
      fetchCatalogs();
    } catch (err: any) {
      console.error('Error bulk uploading PPTP proxies:', err);
      alert(err.response?.data?.detail || 'Failed to bulk upload PPTP proxies');
    }
  };

  const handleSelectOne = (productId: number) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(productId)) {
      newSelected.delete(productId);
    } else {
      newSelected.add(productId);
    }
    setSelectedIds(newSelected);
  };

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) {
      alert('Please select proxies to delete');
      return;
    }

    if (!confirm(`Are you sure you want to delete ${selectedIds.size} proxies?`)) {
      return;
    }

    try {
      setIsDeleting(true);
      const result = await adminApiClient.bulkDeletePptp(Array.from(selectedIds));

      alert(`✅ Deleted ${result.deleted_count} proxies${result.failed_count > 0 ? ` (${result.failed_count} errors)` : ''}`);

      setSelectedIds(new Set());
      fetchCatalogs();
    } catch (err: any) {
      console.error('Error deleting proxies:', err);
      alert(err.response?.data?.detail || 'Failed to delete proxies');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">PPTP Proxies</h1>
        <p className="text-gray-600">Manage PPTP proxy catalogs and inventory</p>
      </div>

      {/* Actions Bar */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
        <div className="flex gap-2">
          {selectedIds.size > 0 && (
            <button
              onClick={handleBulkDelete}
              disabled={isDeleting}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4" />
              Delete Selected ({selectedIds.size})
            </button>
          )}
          <button
            onClick={() => {
              setIsBulkModalOpen(true);
              fetchCatalogsForSelect();
            }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Upload className="w-4 h-4" />
            Bulk Upload
          </button>
        </div>
      </div>

      {/* Catalogs List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : error ? (
          <div className="p-8 text-center text-red-500">{error}</div>
        ) : catalogs.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No catalogs found</div>
        ) : (
          <div className="divide-y divide-gray-200">
            {catalogs.map((catalog) => (
              <div key={catalog.id} className="bg-white">
                {/* Catalog Header */}
                <div
                  className="px-6 py-4 cursor-pointer hover:bg-gray-50 transition-colors flex items-center justify-between"
                  onClick={() => toggleCatalog(catalog.id)}
                >
                  <div className="flex items-center gap-3">
                    {catalog.isExpanded ? (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    )}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{catalog.name}</h3>
                      <p className="text-sm text-gray-500">
                        {catalog.count} proxies • ${catalog.price} per proxy
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <button
                      onClick={(e) => openEditCatalog(catalog, e)}
                      className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Edit catalog"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => handleDeleteCatalog(catalog.id, catalog.name, e)}
                      className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete catalog"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <span className="px-3 py-1 text-sm font-medium bg-blue-100 text-blue-800 rounded-full">
                      ${catalog.price}
                    </span>
                    <span className="text-sm text-gray-500">
                      {catalog.count} items
                    </span>
                  </div>
                </div>

                {/* Catalog Content (Proxies) */}
                {catalog.isExpanded && (
                  <div className="px-6 py-4 bg-gray-50">
                    {catalog.isLoading ? (
                      <div className="text-center text-gray-500 py-4">Loading proxies...</div>
                    ) : !catalog.proxies || catalog.proxies.length === 0 ? (
                      <div className="text-center text-gray-500 py-4">No proxies in this catalog</div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-100">
                            <tr>
                              <th className="px-4 py-2 text-left">
                                <input
                                  type="checkbox"
                                  onChange={(e) => {
                                    const proxyIds = catalog.proxies?.map(p => p.product_id) || [];
                                    if (e.target.checked) {
                                      setSelectedIds(new Set([...selectedIds, ...proxyIds]));
                                    } else {
                                      const newSelected = new Set(selectedIds);
                                      proxyIds.forEach(id => newSelected.delete(id));
                                      setSelectedIds(newSelected);
                                    }
                                  }}
                                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                />
                              </th>
                              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">IP</th>
                              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Login:Password</th>
                              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Country</th>
                              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">State/City</th>
                              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {catalog.proxies.map((proxy) => (
                              <tr key={proxy.product_id} className={selectedIds.has(proxy.product_id) ? 'bg-blue-50' : 'hover:bg-gray-50'}>
                                <td className="px-4 py-3">
                                  <input
                                    type="checkbox"
                                    checked={selectedIds.has(proxy.product_id)}
                                    onChange={() => handleSelectOne(proxy.product_id)}
                                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                  />
                                </td>
                                <td className="px-4 py-3 text-sm font-medium text-gray-900">{proxy.ip}</td>
                                <td className="px-4 py-3 text-xs text-gray-500 font-mono">{proxy.login}:{proxy.password}</td>
                                <td className="px-4 py-3 text-sm text-gray-900">{proxy.country}</td>
                                <td className="px-4 py-3 text-sm text-gray-500">{proxy.state} {proxy.city && `/ ${proxy.city}`}</td>
                                <td className="px-4 py-3 text-sm text-gray-500">{new Date(proxy.created_at).toLocaleDateString()}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Bulk Upload Modal */}
      {isBulkModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Bulk Upload PPTP Proxies</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Format
                </label>
                <select
                  value={bulkFormat}
                  onChange={(e) => setBulkFormat(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="line">Line format (IP:LOGIN:PASS:COUNTRY:STATE:CITY[:ZIP])</option>
                  <option value="csv">CSV format</option>
                </select>
              </div>

              {/* Catalog Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Catalog/Group
                </label>

                {/* Create New Catalog Checkbox */}
                <div className="flex items-center mb-3">
                  <input
                    type="checkbox"
                    id="createNewCatalog"
                    checked={isCreatingNewCatalog}
                    onChange={(e) => {
                      setIsCreatingNewCatalog(e.target.checked);
                      if (e.target.checked) {
                        setSelectedCatalogId(null);
                      }
                    }}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="createNewCatalog" className="ml-2 text-sm text-gray-700">
                    Create New Catalog
                  </label>
                </div>

                {isCreatingNewCatalog ? (
                  // New catalog fields
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">
                        Catalog Name
                      </label>
                      <input
                        type="text"
                        value={newCatalogName}
                        onChange={(e) => setNewCatalogName(e.target.value)}
                        placeholder="e.g., Premium PPTP USA"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">
                        Price (USD)
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        value={newCatalogPrice}
                        onChange={(e) => setNewCatalogPrice(e.target.value)}
                        placeholder="e.g., 5.00"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                ) : (
                  // Existing catalog dropdown
                  <select
                    value={selectedCatalogId || ''}
                    onChange={(e) => setSelectedCatalogId(e.target.value ? parseInt(e.target.value) : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Use default catalog</option>
                    {catalogsForSelect.map((catalog) => (
                      <option key={catalog.id} value={catalog.id}>
                        {catalog.name} (${catalog.price})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Proxy Data (one per line)
                </label>
                <textarea
                  value={bulkData}
                  onChange={(e) => setBulkData(e.target.value)}
                  placeholder="104.11.157.41:user1:pass123:United States:TX:Houston:77001&#10;100.12.0.17:admin:secret:United States:NY:NewYork"
                  rows={15}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                />
                <p className="mt-2 text-sm text-gray-500">
                  Format: IP:LOGIN:PASS:COUNTRY:STATE:CITY[:ZIP]
                  <br />
                  ZIP is optional - you can use 6 or 7 fields
                </p>
              </div>

              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => {
                    setIsBulkModalOpen(false);
                    setBulkData('');
                    setIsCreatingNewCatalog(false);
                    setNewCatalogName('');
                    setNewCatalogPrice('');
                    setSelectedCatalogId(null);
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleBulkUpload}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Upload
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Catalog Modal */}
      {editingCatalog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">Edit Catalog</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Catalog Name
                </label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter catalog name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Price (USD)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={editPrice}
                  onChange={(e) => setEditPrice(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter price"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (RU)
                </label>
                <textarea
                  value={editDescRu}
                  onChange={(e) => setEditDescRu(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={2}
                  placeholder="Russian description (optional)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (EN)
                </label>
                <textarea
                  value={editDescEn}
                  onChange={(e) => setEditDescEn(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={2}
                  placeholder="English description (optional)"
                />
              </div>
            </div>

            <div className="flex gap-2 justify-end mt-6">
              <button
                onClick={() => setEditingCatalog(null)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateCatalog}
                disabled={isUpdatingCatalog}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {isUpdatingCatalog ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Proxies;
