import requests
import logging
from django.conf import settings
import json
import pprint

logger = logging.getLogger(__name__)

class ClubKonnectClient:
    def __init__(self):
        self.base_url = settings.CLUBKONNECT_BASE_URL
        self.user_id = settings.CLUBKONNECT_USER_ID
        self.api_key = settings.CLUBKONNECT_API_KEY
        self.timeout = settings.CLUBKONNECT_TIMEOUT

    def _get_params(self, **kwargs):
        params = {
            "UserID": self.user_id,
            "APIKey": self.api_key,
        }
        params.update(kwargs)
        return params

    def get_airtime_networks(self):
        """
        Fetch airtime networks and discounts.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['airtime_networks']}"
        params = self._get_params()
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect error fetching airtime networks: {e}")
            return {}

    def get_data_plans(self):
        """
        Fetch all data bundles/plans.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['data_plans']}"
        params = self._get_params()
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect error fetching data plans: {e}")
            return {}

    def get_cable_packages(self):
        """
        Fetch all cable/TV packages.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['cable_packages']}"
        params = self._get_params()
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect error fetching cable packages: {e}")
            return {}

    def get_electricity_discos(self):
        """
        Fetch all electricity discos.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['electricity_discos']}"
        params = self._get_params()
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect error fetching electricity discos: {e}")
            return {}

    def get_balance(self):
        """
        Fetch wallet balance.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['balance']}"
        params = self._get_params()
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect error fetching balance: {e}")
            return {}

    def buy_airtime(self, network_id, amount, phone, request_id):
        """
        Purchase airtime.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['buy_airtime']}"
        params = self._get_params(
            MobileNetwork=network_id,
            Amount=amount,
            MobileNumber=phone,
            RequestID=request_id
        )
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            print("ClubKonnect Airtime Purchase Response:", response.text) # TODO: Remove after testing
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect airtime purchase error: {e}")
            return {"status": "error", "message": str(e)}

    def buy_data(self, network_id, plan_id, phone, request_id):
        """
        Purchase data bundle.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['buy_data']}"
        params = self._get_params(
            MobileNetwork=network_id,
            DataPlan=plan_id,
            MobileNumber=phone,
            RequestID=request_id
        )
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect data purchase error: {e}")
            return {"status": "error", "message": str(e)}

    def buy_tv(self, tv_id, package_id, smart_card_number, phone, request_id):
        """
        Purchase TV subscription.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['buy_cable']}"
        params = self._get_params(
            TVModel=tv_id,
            TVPackage=package_id,
            SmartCardNo=smart_card_number,
            MobileNumber=phone,
            RequestID=request_id
        )
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect TV purchase error: {e}")
            return {"status": "error", "message": str(e)}

    def buy_electricity(self, disco_id, plan_id, meter_number, phone, amount, request_id):
        """
        Purchase electricity tokens.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['buy_electricity']}"
        params = self._get_params(
            ElectricCompany=disco_id,
            MeterNo=meter_number,
            MeterType=plan_id, # Usually '01' or '02'
            MobileNumber=phone,
            Amount=amount,
            RequestID=request_id
        )
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect electricity purchase error: {e}")
            return {"status": "error", "message": str(e)}

    def verify_tv(self, tv_id, smart_card_number):
        """
        Verify TV customer.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['verify_cable']}"
        params = self._get_params(
            TVModel=tv_id,
            SmartCardNo=smart_card_number
        )
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect TV verification error: {e}")
            return {"status": "error", "message": str(e)}

    def verify_electricity(self, disco_id, meter_number):
        """
        Verify Electricity customer.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['verify_electricity']}"
        params = self._get_params(
            ElectricCompany=disco_id,
            MeterNo=meter_number
        )
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect electricity verification error: {e}")
            return {"status": "error", "message": str(e)}

    def buy_smile(self, plan_id, phone, request_id, callback_url=None):
        """
        Purchase Smile Data bundle.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['buy_smile']}"
        params = self._get_params(
            MobileNetwork="smile-direct",
            DataPlan=plan_id,
            MobileNumber=phone,
            RequestID=request_id
        )
        if callback_url:
            params["CallBackURL"] = callback_url
            
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect Smile purchase error: {e}")
            return {"status": "error", "message": str(e)}

    def verify_smile(self, phone):
        """
        Verify Smile account.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['verify_smile']}"
        params = self._get_params(
            MobileNetwork="smile-direct",
            MobileNumber=phone
        )
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect Smile verification error: {e}")
            return {"status": "error", "message": str(e)}

    def get_smile_packages(self):
        """
        Fetch all Smile packages.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['smile_packages']}"
        params = self._get_params()
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect error fetching smile packages: {e}")
            return {}

    def sync_airtime(self):
        from orders.models import AirtimeNetwork
        print("Syncing Airtime Networks...")
        airtime_data = self.get_airtime_networks()
        airtime_networks = airtime_data.get("MOBILE_NETWORK", {})
        airtime_count = 0
        for network_name, network_list in airtime_networks.items():
            if not network_list: continue
            net_info = network_list[0]
            products = net_info.get("PRODUCT", [])
            for product in (products if products else [net_info]):
                name = product.get("PRODUCT_NAME") or network_name
                service_id = net_info.get("ID") or product.get("ID") or name.lower()
                AirtimeNetwork.objects.update_or_create(
                    service_id=service_id,
                    defaults={
                        "service_name": name,
                        "min_amount": product.get("MINAMOUNT", "50"),
                        "max_amount": product.get("MAXAMOUNT", "200000"),
                        "discount": product.get("PRODUCT_DISCOUNT", "0"),
                    }
                )
                airtime_count += 1
        print(f"Synced {airtime_count} airtime networks")
        return airtime_count

    def sync_data(self):
        from orders.models import DataService, DataVariation
        print("Syncing Data Packages...")
        data_resp = self.get_data_plans()
        data_networks = data_resp.get("MOBILE_NETWORK", {})
        data_plans_count = 0
        for network_name, network_list in data_networks.items():
            if not network_list: continue
            net_info = network_list[0]
            service_id = net_info.get("ID")
            products = net_info.get("PRODUCT", [])
            service, _ = DataService.objects.get_or_create(
                service_id=service_id,
                defaults={"service_name": network_name}
            )
            for product in products:
                DataVariation.objects.update_or_create(
                    variation_id=product.get("PRODUCT_ID"),
                    defaults={
                        "name": product.get("PRODUCT_NAME"),
                        "service": service,
                        "selling_price": product.get("PRODUCT_AMOUNT", 0),
                        "is_active": True
                    }
                )
                data_plans_count += 1
        print(f"Synced {data_plans_count} data plans")
        return data_plans_count

    def sync_cable(self):
        from orders.models import TVService, TVVariation
        print("Syncing Cable/TV Packages...")
        tv_resp = self.get_cable_packages()
        tv_networks = tv_resp.get("MOBILE_NETWORK") or tv_resp.get("TV_ID") or {}
        tv_packages_count = 0
        for network_name, network_list in tv_networks.items():
            if not network_list: continue
            net_info = network_list[0]
            service_id = net_info.get("ID") or network_name.lower().replace(" ", "-")
            products = net_info.get("PRODUCT") or net_info.get("PACKAGE") or []
            
            service, _ = TVService.objects.get_or_create(
                service_id=service_id,
                defaults={"service_name": network_name}
            )
            
            for product in products:
                TVVariation.objects.update_or_create(
                    variation_id=product.get("PACKAGE_ID") or product.get("PRODUCT_ID"),
                    defaults={
                        "name": product.get("PACKAGE_NAME") or product.get("PRODUCT_NAME"),
                        "service": service,
                        "selling_price": product.get("PACKAGE_AMOUNT") or product.get("PRODUCT_AMOUNT") or 0,
                        "package_bouquet": product.get("PACKAGE_NAME") or product.get("PRODUCT_NAME"),
                        "is_active": True
                    }
                )
                tv_packages_count += 1
        print(f"Synced {tv_packages_count} cable/tv packages")
        return tv_packages_count

    def sync_electricity(self):
        from orders.models import ElectricityService, ElectricityVariation
        print("Syncing Electricity Services...")
        electricity_resp = self.get_electricity_discos()
        electricity_networks = electricity_resp.get("MOBILE_NETWORK") or electricity_resp.get("ELECTRIC_COMPANY") or {}
        electricity_count = 0
        for network_name, network_list in electricity_networks.items():
            if not network_list: continue
            net_info = network_list[0]
            raw_id = net_info.get("ID")
            service_id = raw_id if (raw_id and not raw_id.isdigit()) else network_name.lower().replace("_", "-").replace(" ", "-")
            
            products = net_info.get("PRODUCT") or []
            
            service, _ = ElectricityService.objects.get_or_create(
                service_id=service_id,
                defaults={"service_name": net_info.get("NAME") or network_name.replace("_", " ").title()}
            )
            
            for product in products:
                ElectricityVariation.objects.update_or_create(
                    variation_id=product.get("PRODUCT_ID"),
                    service=service,
                    defaults={
                        "name": product.get("PRODUCT_TYPE", "General").capitalize(),
                        "is_active": True
                    }
                )
                electricity_count += 1
        print(f"Synced {electricity_count} electricity variations")
        return electricity_count

    def sync_smile(self):
        from orders.models import SmileVariation
        print("Syncing Smile Packages...")
        smile_resp = self.get_smile_packages()
        smile_networks = smile_resp.get("MOBILE_NETWORK") or {}
        smile_count = 0
        for network_name, network_list in smile_networks.items():
            if not network_list: continue
            net_info = network_list[0]
            products = net_info.get("PRODUCT") or []
            
            for product in products:
                # Smile response uses PACKAGE_ID, PACKAGE_NAME, etc.
                variation_id = product.get("PACKAGE_ID") or product.get("PRODUCT_ID")
                name = product.get("PACKAGE_NAME") or product.get("PRODUCT_NAME")
                amount = product.get("PACKAGE_AMOUNT") or product.get("PRODUCT_AMOUNT") or 0
                
                if not variation_id or not name:
                    continue

                SmileVariation.objects.update_or_create(
                    variation_id=variation_id,
                    defaults={
                        "name": name,
                        "selling_price": amount,
                        "is_active": True
                    }
                )
                smile_count += 1
        print(f"Synced {smile_count} smile packages")
        return smile_count

    def query_transaction(self, order_id=None, request_id=None):
        """
        Query transaction status by OrderID or RequestID.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['query']}"
        params = {}
        if order_id:
            params["OrderID"] = order_id
        elif request_id:
            params["RequestID"] = request_id
        else:
            return {"status": "error", "message": "Either OrderID or RequestID must be provided"}
            
        params = self._get_params(**params)
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect query error: {e}")
            return {"status": "error", "message": str(e)}

    def cancel_transaction(self, order_id):
        """
        Cancel transaction by OrderID.
        """
        url = f"{self.base_url}{settings.CLUBKONNECT_ENDPOINTS['cancel']}"
        params = self._get_params(OrderID=order_id)
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect cancel error: {e}")
            return {"status": "error", "message": str(e)}

    def sync_all_services(self):
        """
        Main function to fetch all services and populate the database.
        """
        self.sync_airtime()
        self.sync_data()
        self.sync_cable()
        self.sync_electricity()
        self.sync_smile()
        
        return True

