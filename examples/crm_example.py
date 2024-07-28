import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

from smartgraph.tools.duck_memory_toolkit import DuckMemoryToolkit


class RefinedCRMSystem:
    def __init__(self):
        self.memory = DuckMemoryToolkit("new_crm_database.duckdb")

    async def add_customer(
        self, customer_id: str, name: str, email: str, company: str, created_at: str = None
    ):  # noqa: PLR0913
        customer_data = {
            "name": name,
            "email": email,
            "company": company,
            "created_at": created_at or datetime.now().isoformat(),
            "last_contact": None,
            "notes": [],
            "deals": [],
        }
        await self.memory.add_memory(f"customer:{customer_id}", customer_data)
        print(f"Added customer: {name} from {company}")

    async def update_customer_contact(self, customer_id: str, note: str, contact_time: str = None):
        customer = await self.memory.get_memory(f"customer:{customer_id}")
        if customer:
            customer["last_contact"] = contact_time or datetime.now().isoformat()
            customer["notes"].append({"date": customer["last_contact"], "note": note})
            await self.memory.add_memory(f"customer:{customer_id}", customer)
            print(f"Updated contact info for customer: {customer['name']}")
        else:
            print(f"Customer with ID {customer_id} not found")

    async def add_deal(
        self, customer_id: str, deal_name: str, value: float, created_at: str = None
    ):
        customer = await self.memory.get_memory(f"customer:{customer_id}")
        if customer:
            deal = {
                "name": deal_name,
                "value": value,
                "status": "Pending",
                "created_at": created_at or datetime.now().isoformat(),
            }
            customer["deals"].append(deal)
            await self.memory.add_memory(f"customer:{customer_id}", customer)
            print(f"Added new deal '{deal_name}' for customer: {customer['name']}")
        else:
            print(f"Customer with ID {customer_id} not found")

    async def search_customers(self, query: str) -> List[Dict[str, Any]]:
        results = await self.memory.search_memories(query)
        found_customers = []
        for result in results:
            if result["key"].startswith("customer:"):
                customer = result["value"]
                found_customers.append(customer)
                self._print_customer_info(customer)
        return found_customers

    async def search_high_value_deals(self, threshold: float) -> List[Dict[str, Any]]:
        all_customers = await self.memory.search_memories("customer:")
        high_value_customers = []
        for result in all_customers:
            customer = result["value"]
            for deal in customer["deals"]:
                if deal["value"] > threshold:
                    high_value_customers.append(customer)
                    print(f"High-value deal found for {customer['name']}:")
                    self._print_customer_info(customer)
                    print(f"Deal: {deal['name']}, Value: ${deal['value']}")
                    print("---")
                    break  # Break after finding the first high-value deal for this customer
        return high_value_customers

    async def get_customers_needing_followup(self, hours: int) -> List[Dict[str, Any]]:
        all_customers = await self.memory.search_memories("customer:")
        followup_customers = []
        threshold_date = datetime.now() - timedelta(hours=hours)
        for result in all_customers:
            customer = result["value"]
            last_contact = (
                datetime.fromisoformat(customer["last_contact"])
                if customer["last_contact"]
                else None
            )
            if not last_contact or last_contact < threshold_date:
                followup_customers.append(customer)
                print("Customer needing follow-up:")
                self._print_customer_info(customer)
        return followup_customers

    def _print_customer_info(self, customer: Dict[str, Any]):
        print(f"Customer: {customer['name']}, Company: {customer['company']}")
        print(f"Email: {customer['email']}")
        print(f"Last Contact: {self.format_date(customer['last_contact'])}")
        print(f"Deals: {len(customer['deals'])}")
        print("---")

    @staticmethod
    def format_date(date_string: str) -> str:
        if not date_string:
            return "Never contacted"
        date = datetime.fromisoformat(date_string)
        return date.strftime("%Y-%m-%d %H:%M:%S")


async def main():
    crm = RefinedCRMSystem()

    print("Initializing CRM System...")
    # Add customers with specific creation dates
    await crm.add_customer(
        "001", "John Doe", "john@techcorp.com", "TechCorp", created_at="2024-07-20T10:00:00"
    )
    await crm.add_customer(
        "002",
        "Jane Smith",
        "jane@innovatesolutions.com",
        "Innovate Solutions",
        created_at="2024-07-22T14:00:00",
    )
    await crm.add_customer(
        "003", "Bob Johnson", "bob@megasoft.com", "MegaSoft", created_at="2024-07-24T09:00:00"
    )

    # Update customer contacts with specific times
    await crm.update_customer_contact(
        "001", "Discussed new project requirements", contact_time="2024-07-25T11:00:00"
    )
    await crm.update_customer_contact(
        "002", "Scheduled demo for next week", contact_time="2024-07-26T13:00:00"
    )
    # Note: Bob Johnson is intentionally left without a contact update

    # Add deals
    await crm.add_deal("001", "Custom ERP System", 50000, created_at="2024-07-25T15:00:00")
    await crm.add_deal("002", "Mobile App Development", 30000, created_at="2024-07-26T10:00:00")
    await crm.add_deal("003", "Cloud Migration Service", 75000, created_at="2024-07-24T16:00:00")

    print("\n1. Searching for customers with 'Tech' in their data:")
    await crm.search_customers("Tech")

    print("\n2. Searching for customers with high-value deals (over $40000):")
    await crm.search_high_value_deals(40000)

    print("\n3. Customers needing follow-up (not contacted in the last 48 hours):")
    await crm.get_customers_needing_followup(48)


if __name__ == "__main__":
    asyncio.run(main())
