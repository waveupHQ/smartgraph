import asyncio
from typing import Any, Dict

from reactivex import Observable, create
from reactivex import operators as ops
from reactivex.scheduler import NewThreadScheduler
from reactivex.subject import Subject

from smartgraph.logging import SmartGraphLogger

logger = SmartGraphLogger.get_logger()


class FinancialTransactionPipeline:
    def __init__(self):
        self.input_subject = Subject()

    def process_transaction(self, input_data: Dict[str, Any]) -> Observable:
        return self.input_subject.pipe(
            ops.map(self.verify_account),
            ops.map(self.prepare_transaction),
            ops.flat_map(self.request_approval),
            ops.filter(lambda x: x["approved"]),
            ops.map(self.execute_transaction),
        )

    def verify_account(self, data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Verifying account: {data['account_id']}")
        return {**data, "account_verified": True, "balance": 1000.00}

    def prepare_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Preparing transaction: ${data['amount']:.2f}")
        return {**data, "transaction_id": "TX123456", "fee": data["amount"] * 0.01}

    def request_approval(self, data: Dict[str, Any]) -> Observable:
        def approval_input(observer, scheduler):
            print("\nApproval required for transaction:")
            print(f"Transaction ID: {data['transaction_id']}")
            print(f"Amount: ${data['amount']:.2f}")
            print(f"Fee: ${data['fee']:.2f}")

            user_input = input("Do you approve this transaction? (yes/no): ").lower()
            approved = user_input in ("yes", "y")
            observer.on_next({**data, "approved": approved})
            observer.on_completed()

        return create(approval_input)

    def execute_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing transaction: {data['transaction_id']}")
        return {
            **data,
            "status": "completed",
            "new_balance": data["balance"] - data["amount"] - data["fee"],
        }


def main():
    pipeline = FinancialTransactionPipeline()

    def on_next(x):
        if x["approved"]:
            print("\nFinal Result:")
            print(f"Transaction Status: {x['status']}")
            print(f"Transaction ID: {x['transaction_id']}")
            print(f"New Balance: ${x['new_balance']:.2f}")
        else:
            print("\nTransaction was not approved.")

    def on_error(err):
        print(f"An error occurred: {err}")

    def on_completed():
        print("Transaction processing completed.")

    input_data = {"account_id": "ACC987654", "amount": 500.00}

    pipeline.process_transaction(input_data).subscribe(
        on_next=on_next, on_error=on_error, on_completed=on_completed
    )

    pipeline.input_subject.on_next(input_data)


if __name__ == "__main__":
    main()
