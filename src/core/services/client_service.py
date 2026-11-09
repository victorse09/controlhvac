import os
import shutil
from typing import List, Optional

from src.core.models.client import Client, InstallationSite
from src.data.json_storage import JsonStorageEngine


class ClientService:
    """Service for managing Clients and Installation Sites."""

    def __init__(self, storage: JsonStorageEngine, recycle_bin_service=None):
        self.storage = storage
        self.recycle_bin_service = recycle_bin_service

    def save_client(self, client: Client) -> Client:
        self.storage.save_document("clients", client.id, "client.json", client.to_dict())
        self.storage.update_index("clients", client.id, {
            "name": client.name,
            "tax_id": client.tax_id,
            "email": client.email
        })
        return client

    def get_client(self, client_id: str) -> Optional[Client]:
        data = self.storage.load_document("clients", client_id, "client.json")
        return Client.from_dict(data) if data else None

    def get_all_clients(self) -> List[Client]:
        clients = []
        index = self.storage.get_index("clients")
        for client_id in index:
            client = self.get_client(client_id)
            if client:
                clients.append(client)
        return clients

    def delete_client(self, client_id: str) -> bool:
        client = self.get_client(client_id)
        if not client:
            return False
            
        sites = self.get_sites_for_client(client_id)
        if self.recycle_bin_service:
            self.recycle_bin_service.recycle_item(client.id, "CLIENT", client.company_name, client.to_dict())
            for s in sites:
                self.recycle_bin_service.recycle_item(s.id, "SITE", s.name, s.to_dict(), {"client_id": client_id})
        
        client_dir = os.path.join(self.storage.base_path, "clients", client_id)
        try:
            if os.path.exists(client_dir):
                shutil.rmtree(client_dir)
        except Exception:
            return False
        
        self.storage.remove_from_index("clients", client_id)
        return True

    def search_clients(self, query: str) -> List[Client]:
        query = query.lower()
        results = []
        for client in self.get_all_clients():
            if (query in client.name.lower() or 
                query in client.tax_id.lower() or 
                query in client.email.lower() or 
                query in (client.phone or "").lower()):
                results.append(client)
        return results

    def save_site(self, site: InstallationSite) -> InstallationSite:
        client_id = site.client_id
        path = f"clients/{client_id}/sites"
        self.storage.save_document(path, site.id, "site.json", site.to_dict())
        return site

    def get_sites_for_client(self, client_id: str) -> List[InstallationSite]:
        sites = []
        sites_dir = os.path.join(self.storage.base_path, "clients", client_id, "sites")
        if not os.path.exists(sites_dir):
            return sites
            
        path = f"clients/{client_id}/sites"
        for site_id in os.listdir(sites_dir):
            data = self.storage.load_document(path, site_id, "site.json")
            if data:
                sites.append(InstallationSite.from_dict(data))
        return sites

    def get_site(self, site_id: str, client_id: str) -> Optional[InstallationSite]:
        path = f"clients/{client_id}/sites"
        data = self.storage.load_document(path, site_id, "site.json")
        return InstallationSite.from_dict(data) if data else None

    def delete_site(self, site_id: str, client_id: str) -> bool:
        site = self.get_site(site_id, client_id)
        if site and self.recycle_bin_service:
            self.recycle_bin_service.recycle_item(site.id, "SITE", site.name, site.to_dict(), {"client_id": client_id})

        site_dir = os.path.join(self.storage.base_path, "clients", client_id, "sites", site_id)
        try:
            if os.path.exists(site_dir):
                shutil.rmtree(site_dir)
                return True
        except Exception:
            pass
        return False

    def get_all_sites(self) -> List[InstallationSite]:
        all_sites = []
        for client in self.get_all_clients():
            all_sites.extend(self.get_sites_for_client(client.id))
        return all_sites
