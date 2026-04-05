import requests
import json
import logging
from typing import Dict, Any, Optional, List
from ..interfaces import BaseVTUProvider

logger = logging.getLogger(__name__)

class ClubKonnectProvider(BaseVTUProvider):
    """
    ClubKonnect implementation of BaseVTUProvider.
    """

    def __init__(self, config: Dict[str, Any]):
        self.user_id = config.get('user_id')
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url')
        if self.base_url is None or self.base_url == '':
            self.base_url = 'https://www.nellobytesystems.com'
            
        self.headers = {
            "Content-Type": "application/json",
        }

    @property
    def provider_name(self) -> str:
        return "clubkonnect"

    @classmethod
    def get_supported_services(cls) -> List[str]:
        return ["airtime", "data", "tv", "electricity", "education", "internet"]

    @classmethod
    def get_config_requirements(cls) -> List[Dict[str, Any]]:
        return [
            {"name": "user_id", "label": "User ID", "type": "text", "required": True},
            {"name": "api_key", "label": "API Key", "type": "text", "required": True},
            {"name": "base_url", "label": "Base URL", "type": "text", "required": False, "default": "https://www.nellobytesystems.com"},
        ]

    def _get(self, endpoint: str, params: dict) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        params.update({"UserID": self.user_id, "APIKey": self.api_key})
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"ClubKonnect request error: {str(e)}")
            raise Exception(f"ClubKonnect API error: {str(e)}")

    def buy_airtime(self, phone: str, network: str, amount: float, reference: str) -> Dict[str, Any]:
        # network map for ClubKonnect
        network_map = {'mtn': '01', 'glo': '02', 'airtel': '03', '9mobile': '04'}
        service_id = network_map.get(network.lower(), '01')
        
        params = {
            "MobileNetwork": service_id,
            "Amount": int(amount),
            "MobileNumber": phone,
            "RequestID": reference
        }
        res = self._get("/Airtime.asp", params)
        
        status = "PENDING"
        if res.get('status') == 'ORDER_COMPLETED':
            status = "SUCCESS"
        elif res.get('status') in ['ORDER_FAILED', 'ORDER_CANCELLED']:
            status = "FAILED"
            
        return {
            "status": status,
            "provider_reference": res.get('orderid'),
            "message": res.get('remark'),
            "raw_response": res
        }

    def buy_data(self, phone: str, network: str, plan_id: str, amount: float, reference: str) -> Dict[str, Any]:
        network_map = {'mtn': '01', 'glo': '02', 'airtel': '03', '9mobile': '04'}
        service_id = network_map.get(network.lower(), '01')
        
        params = {
            "MobileNetwork": service_id,
            "DataPlan": plan_id,
            "MobileNumber": phone,
            "RequestID": reference
        }
        res = self._get("/Data.asp", params)
        
        status = "PENDING"
        if res.get('status') == 'ORDER_COMPLETED':
            status = "SUCCESS"
        elif res.get('status') in ['ORDER_FAILED', 'ORDER_CANCELLED']:
            status = "FAILED"
            
        return {
            "status": status,
            "provider_reference": res.get('orderid'),
            "message": res.get('remark'),
            "raw_response": res
        }

    def pay_bill(self, service_type: str, identifier: str, amount: float, plan_id: str, reference: str, metadata: dict = None) -> Dict[str, Any]:
        # service_type for CK usually includes 'CableTV', 'Electricity'
        params = {
            "MobileNumber": identifier,
            "Amount": int(amount),
            "RequestID": reference
        }
        # CK uses different endpoints for different services
        if service_type.lower() in ['dstv', 'gotv', 'startimes']:
             endpoint = "/CableTV.asp"
             params.update({"CableTV": service_type, "Package": plan_id})
        else:
             endpoint = "/Electricity.asp"
             params.update({"ElectricCompany": service_id, "MeterNo": identifier, "MeterType": "01"}) # PREPAID

        res = self._get(endpoint, params)
        
        status = "PENDING"
        if res.get('status') == 'ORDER_COMPLETED':
            status = "SUCCESS"
        elif res.get('status') in ['ORDER_FAILED', 'ORDER_CANCELLED']:
            status = "FAILED"
            
        return {
            "status": status,
            "provider_reference": res.get('orderid'),
            "message": res.get('remark'),
            "raw_response": res
        }

    def query_transaction(self, reference: str) -> Dict[str, Any]:
        res = self._get("/Query.asp", {"RequestID": reference})
        
        status = "PENDING"
        if res.get('status') == 'ORDER_COMPLETED':
            status = "SUCCESS"
        elif res.get('status') in ['ORDER_FAILED', 'ORDER_CANCELLED']:
            status = "FAILED"
            
        return {
            "status": status,
            "raw_response": res
        }

    def handle_webhook(self, data: Dict[str, Any]) -> bool:
        """Processes ClubKonnect webhook notifications."""
        return self._process_async_feedback(data)

    def handle_callback(self, data: Dict[str, Any]) -> bool:
        """Processes ClubKonnect callback notifications."""
        return self._process_async_feedback(data)

    def _process_async_feedback(self, data: Dict[str, Any]) -> bool:
        """Unified processing for ClubKonnect async feedback."""
        from orders.models import Purchase
        
        order_id = data.get("orderid") or data.get("OrderID")
        request_id = data.get("requestid") or data.get("RequestID")
        status_code = data.get("statuscode") or data.get("StatusCode") or data.get("Status")
        
        logger.info(f"ClubKonnect Async Feedback: order_id={order_id}, request_id={request_id}, status={status_code}")

        try:
            purchase = Purchase.objects.filter(reference__in=[order_id, request_id]).first()
            if not purchase:
                logger.warning(f"ClubKonnect Feedback: Purchase not found for reference {order_id or request_id}")
                return False

            purchase.provider_response = data
            
            if status_code in ["200", "delivered", "Success"]:
                purchase.status = "success"
                purchase.save()
            elif status_code in ["100", "101", "102", "pending", "Pending"]:
                # Keep as pending
                pass
            else:
                self._handle_async_failure(purchase, f"ClubKonnect reported failure: {status_code}")

            return True
        except Exception as e:
            logger.error(f"ClubKonnect Feedback Error: {e}")
            return False

    def _handle_async_failure(self, purchase, error_msg):
        """Internal failure handling delegating to common logic."""
        purchase.last_error = error_msg
        purchase.save()
        
        from orders.utils.purchase_logic import handle_vtu_async_failure
        handle_vtu_async_failure(purchase)

    def validate_meter(self, meter_number: str, service: str) -> Dict[str, Any]:
        params = {"ElectricCompany": service, "MeterNo": meter_number}
        res = self._get("/ElectricityVerify.asp", params)
        return {
            "account_name": res.get('customername'),
            "raw_response": res
        }

    def validate_cable_id(self, card_number: str, service: str) -> Dict[str, Any]:
        params = {"CableTV": service, "SmartCardNo": card_number}
        res = self._get("/CableTVVerify.asp", params)
        return {
            "account_name": res.get('customername'),
            "raw_response": res
        }

    def get_wallet_balance(self) -> float:
        res = self._get("/APIWalletBalanceV1.asp", {})
        return res.get('balance', 0)

    def get_available_services(self) -> List[Dict[str, Any]]:
        """
        Returns a list of available services, networks, and variations from ClubKonnect.
        """
        return [
            {"type": "airtime", "endpoint": "/AirtimeNetworks.asp"},
            {"type": "data", "endpoint": "/DataPlans.asp"},
            {"type": "cable", "endpoint": "/CableTVPackages.asp"},
            {"type": "electricity", "endpoint": "/ElectricityCompanies.asp"},
            {"type": "internet", "endpoint": "/SmilePackages.asp"},
            {"type": "education", "endpoint": "/EducationPackages.asp"},
        ]
    
    def get_airtime_networks(self) -> List[Any]:
        res = self._get("/APIAirtimeDiscountV2.asp", {})
        networks = res.get("MOBILE_NETWORK") or {}
        created_networks = []
        for network_name, product_list in networks.items():
            if not product_list: continue
            created_networks.extend(self._deserialize_airtime(network_name, product_list))
        return created_networks

    def _deserialize_airtime(self, network_name: str, product_list: List[Dict]) -> List[Any]:
        from orders.models import AirtimeNetwork
        created = []
        for product in product_list:
            discount = product.get("PRODUCT_DISCOUNT", "0")
            if isinstance(discount, str):
                discount = discount.replace("%", "").strip()
            
            net, _ = AirtimeNetwork.objects.update_or_create(
                service_id=product.get("ID"),
                defaults={
                    "service_name": product.get("PRODUCT_NAME", network_name).capitalize(),
                    "min_amount": product.get("MINAMOUNT", "50"),
                    "max_amount": product.get("MAXAMOUNT", "200000"),
                    "discount": discount,
                    "provider": getattr(self, "provider_config", None),
                }
            )
            created.append(net)
        return created

    def get_data_plans(self, network_id: Optional[str] = None) -> List[Any]:
        params = {"MobileNetwork": network_id} if network_id else {}
        res = self._get("/APIDatabundlePlansV2.asp", params)
        networks = res.get("MOBILE_NETWORK") or {}
        created_variations = []
        for network_name, network_list in networks.items():
            if not network_list: continue
            created_variations.extend(self._deserialize_data(network_name, network_list))
        return created_variations

    def _deserialize_data(self, network_name: str, network_list: List[Dict]) -> List[Any]:
        from orders.models import DataService, DataVariation
        created = []
        net_info = network_list[0]
        service_id = net_info.get("ID")
        products = net_info.get("PRODUCT", [])
        service, _ = DataService.objects.get_or_create(
            service_id=service_id,
            defaults={"service_name": network_name, "provider": getattr(self, "provider_config", None)}
        )
        for product in products:
            variation, _ = DataVariation.objects.update_or_create(
                variation_id=product.get("PRODUCT_ID"),
                service=service,
                defaults={
                    "name": product.get("PRODUCT_NAME", "Data Plan"),
                    "selling_price": product.get("PRODUCT_AMOUNT", product.get("selling_price", 0)),
                    "is_active": True
                }
            )
            created.append(variation)
        return created

    def get_cable_tv_packages(self, service_id: Optional[str] = None) -> List[Any]:
        params = {"CableTV": service_id} if service_id else {}
        res = self._get("/APICableTVPackagesV2.asp", params)
        networks = res.get("MOBILE_NETWORK") or res.get("TV_ID") or res.get("CABLETV") or {}
        created_variations = []
        for network_name, network_list in networks.items():
            if not network_list: continue
            created_variations.extend(self._deserialize_tv(network_name, network_list))
        return created_variations

    def _deserialize_tv(self, network_name: str, network_list: List[Dict]) -> List[Any]:
        from orders.models import TVService, TVVariation
        created = []
        net_info = network_list[0]
        s_id = net_info.get("ID") or network_name.lower().replace(" ", "-")
        products = net_info.get("PRODUCT") or net_info.get("PACKAGE") or []
        service, _ = TVService.objects.get_or_create(
            service_id=s_id,
            defaults={"service_name": network_name, "provider": getattr(self, "provider_config", None)}
        )
        for product in products:
            variation, _ = TVVariation.objects.update_or_create(
                variation_id=product.get("PACKAGE_ID") or product.get("PRODUCT_ID"),
                service=service,
                defaults={
                    "name": product.get("PACKAGE_NAME") or product.get("PRODUCT_NAME") or "TV Package",
                    "selling_price": product.get("PACKAGE_AMOUNT") or product.get("PRODUCT_AMOUNT") or 0,
                    "package_bouquet": product.get("PACKAGE_NAME") or product.get("PRODUCT_NAME"),
                    "is_active": True
                }
            )
            created.append(variation)
        return created

    def get_electricity_services(self) -> List[Any]:
        res = self._get("/APIElectricityDiscosV2.asp", {})
        companies = res.get("ELECTRIC_COMPANY") or res.get("ELECTRICCOMPANIES") or {}
        created_variations = []
        for name, company_infos in companies.items():
            if not company_infos: continue
            created_variations.extend(self._deserialize_electricity(name, company_infos))
        return created_variations

    def _deserialize_electricity(self, name: str, company_infos: List[Dict]) -> List[Any]:
        from orders.models import ElectricityService, ElectricityVariation
        created = []
        for company_info in company_infos:
            service, _ = ElectricityService.objects.get_or_create(
                service_id=company_info.get('ID') or name.lower().replace("_", "-").replace(" ", "-"),
                defaults={"service_name": company_info.get("NAME") or name.replace("_", " ").title(), "provider": getattr(self, "provider_config", None)}
            )
            for product in company_info.get("PRODUCT", []):
                variation, _ = ElectricityVariation.objects.update_or_create(
                    variation_id=product.get("PRODUCT_ID"),
                    service=service,
                    defaults={
                        "name": product.get("PRODUCT_TYPE", "General").capitalize(),
                        "min_amount": product.get("MINAMOUNT", "1000"),
                        "max_amount": product.get("MAXAMOUNT", "200000"),
                        "discount": product.get("PRODUCT_DISCOUNT_AMOUNT", "0"),
                        "is_active": True
                    }
                )
                created.append(variation)
        return created

    def get_internet_packages(self) -> List[Any]:
        # res = self._get("/APISmileDiscountV1.asp", {}) 
        # internet_networks = res.get("MOBILE_NETWORK") or {}
        
        # We explicitly return the InternetService object(s) created
        services = []
        # for network_name, network_list in internet_networks.items():
        #     if not network_list: continue
        #     service = self._deserialize_internet(network_name, network_list)
        #     if service:
        #         services.append(service)
        return services

    def _deserialize_internet(self, network_name: str, network_list: List[Dict]) -> Optional[Any]:
        from orders.models import InternetVariation, InternetService
        net_info = network_list[0]
        products = net_info.get("PRODUCT") or []
        service, _ = InternetService.objects.get_or_create(
            service_id=network_name.lower().replace(" ", "-"),
            defaults={"service_name": network_name, "provider": getattr(self, "provider_config", None)}
        )
        for product in products:
            variation_id = product.get("PACKAGE_ID") or product.get("PRODUCT_ID")
            p_name = product.get("PACKAGE_NAME") or product.get("PRODUCT_NAME")
            amount = product.get("PACKAGE_AMOUNT") or product.get("PRODUCT_AMOUNT") or 0
            if not variation_id or not p_name: continue
            InternetVariation.objects.update_or_create(
                variation_id=variation_id,
                defaults={
                    "name": p_name,
                    "service": service,
                    "selling_price": amount,
                    "is_active": True
                }
            )
        return service

    def get_education_services(self) -> List[Any]:
        return []
