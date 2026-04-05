"""
Management command to seed the database with sample data.

Usage:
    python manage.py seed_db              # Seed with default amounts
    python manage.py seed_db --users 20   # Customize user count
    python manage.py seed_db --flush      # Clear existing data first
"""
import random
import uuid
from decimal import Decimal
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


FIRST_NAMES = [
    "Aisha", "Bello", "Chidinma", "Damilola", "Emeka", "Fatima", "Godwin",
    "Halima", "Ibrahim", "Juliet", "Kehinde", "Lateef", "Maryam", "Ngozi",
    "Oluwaseun", "Peter", "Quadri", "Rashidat", "Suleiman", "Tunde",
    "Uche", "Victor", "Wale", "Yetunde", "Zainab",
]

LAST_NAMES = [
    "Abubakar", "Balogun", "Chukwu", "Danjuma", "Ekwueme", "Farouk",
    "Garba", "Hassan", "Igwe", "Jimoh", "Kalu", "Lawal", "Mohammed",
    "Nwosu", "Okonkwo", "Peterside", "Rabiu", "Sanni", "Tanko",
    "Usman", "Vandi", "Williams", "Yakubu", "Zuma", "Adeyemi",
]


class Command(BaseCommand):
    help = "Seed the database with realistic sample data for development and testing."

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=15, help="Number of users to create")
        parser.add_argument("--flush", action="store_true", help="Delete all seeded data before re-seeding")

    def handle(self, *args, **options):
        num_users = options["users"]
        flush = options["flush"]

        if flush:
            self._flush()

        self.stdout.write(self.style.MIGRATE_HEADING("\n🌱 Seeding database...\n"))

        users = self._seed_users(num_users)
        self._seed_wallets(users)
        self._seed_wallet_transactions(users)
        self._seed_deposits(users)
        self._seed_withdrawals(users)
        self._seed_purchases(users)
        self._seed_support_tickets(users)
        self._seed_notifications(users)
        self._seed_announcements()
        self._seed_referrals(users)

        self.stdout.write(self.style.SUCCESS("\n✅ Database seeded successfully!\n"))

    # ─────────────────────────────────────────
    # Flush
    # ─────────────────────────────────────────

    def _flush(self):
        from wallet.models import Wallet, WalletTransaction
        from payments.models import Deposit, Withdrawal
        from orders.models import Purchase
        from support.models import SupportTicket, TicketMessage
        from notifications.models import Notification, UserNotification, Announcement
        from users.models import Referral

        self.stdout.write("  Flushing existing seed data...")
        TicketMessage.objects.all().delete()
        SupportTicket.objects.all().delete()
        UserNotification.objects.all().delete()
        Notification.objects.all().delete()
        Announcement.objects.all().delete()
        Purchase.objects.all().delete()
        Withdrawal.objects.all().delete()
        Deposit.objects.all().delete()
        WalletTransaction.objects.all().delete()
        Wallet.objects.all().delete()
        Referral.objects.all().delete()
        # Delete non-staff, non-superuser seeded users
        User.objects.filter(is_superuser=False, is_staff=False).delete()
        self.stdout.write(self.style.WARNING("  ⚠  Flushed all seeded data."))

    # ─────────────────────────────────────────
    # Users
    # ─────────────────────────────────────────

    def _seed_users(self, count):
        self.stdout.write(f"  Creating {count} users...")
        users = []
        existing_phones = set(User.objects.values_list("phone_number", flat=True))

        for i in range(count):
            phone = self._unique_phone(existing_phones)
            existing_phones.add(phone)

            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            role = random.choices(["customer", "agent", "customer"], weights=[70, 20, 10])[0]

            user = User.objects.create_user(
                phone_number=phone,
                password="1234",
                first_name=first,
                last_name=last,
                email=f"{first.lower()}.{last.lower()}{random.randint(1,999)}@example.com",
                role=role,
                is_active=True,
                is_verified=True,
            )
            if role == "agent":
                user.agent_commission_rate = Decimal(str(random.choice([2.0, 3.0, 5.0])))
                user.save(update_fields=["agent_commission_rate"])

            users.append(user)

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(users)} users created"))
        return users

    # ─────────────────────────────────────────
    # Wallets
    # ─────────────────────────────────────────

    def _seed_wallets(self, users):
        from wallet.models import Wallet

        self.stdout.write("  Creating wallets...")
        created = 0
        for user in users:
            _, was_created = Wallet.objects.get_or_create(
                user=user,
                defaults={"balance": Decimal(str(random.randint(500, 50000)))}
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"    ✓ {created} wallets created"))

    # ─────────────────────────────────────────
    # Wallet Transactions
    # ─────────────────────────────────────────

    def _seed_wallet_transactions(self, users):
        from wallet.models import WalletTransaction, Wallet

        self.stdout.write("  Creating wallet transactions...")
        tx_types = [
            ("credit", "Wallet funded via Paystack"),
            ("credit", "Referral Bonus"),
            ("credit", "Cashback reward"),
            ("credit", "Admin manual credit"),
            ("credit", "Refund for failed transaction"),
            ("debit", "Airtime purchase"),
            ("debit", "Data purchase"),
            ("debit", "Electricity payment"),
            ("debit", "Withdrawal request"),
            ("debit", "TV subscription"),
        ]
        count = 0
        for user in users:
            wallet = Wallet.objects.filter(user=user).first()
            if not wallet:
                continue

            num_tx = random.randint(3, 12)
            running_balance = float(wallet.balance)

            for _ in range(num_tx):
                tx_type, desc = random.choice(tx_types)
                amount = round(random.uniform(50, 5000), 2)

                if tx_type == "debit" and running_balance < amount:
                    tx_type = "credit"
                    desc = "Wallet funded via Paystack"

                balance_before = running_balance
                if tx_type == "credit":
                    running_balance += amount
                else:
                    running_balance -= amount

                days_ago = random.randint(0, 60)
                WalletTransaction.objects.create(
                    user=user,
                    wallet=wallet,
                    transaction_type=tx_type,
                    amount=Decimal(str(amount)),
                    balance_before=Decimal(str(round(balance_before, 2))),
                    balance_after=Decimal(str(round(running_balance, 2))),
                    description=desc,
                    initiator=random.choice(["self", "admin"]) if tx_type == "credit" else "self",
                    status="success",
                    reference=uuid.uuid4().hex[:12].upper(),
                    timestamp=timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23)),
                )
                count += 1

            # Update wallet balance to match
            wallet.balance = Decimal(str(round(running_balance, 2)))
            wallet.save(update_fields=["balance"])

        self.stdout.write(self.style.SUCCESS(f"    ✓ {count} wallet transactions created"))

    # ─────────────────────────────────────────
    # Deposits
    # ─────────────────────────────────────────

    def _seed_deposits(self, users):
        from payments.models import Deposit

        self.stdout.write("  Creating deposits...")
        count = 0
        for user in users:
            num = random.randint(0, 5)
            for _ in range(num):
                status = random.choices(["SUCCESS", "PENDING", "FAILED"], weights=[70, 20, 10])[0]
                days_ago = random.randint(0, 45)
                Deposit.objects.create(
                    user=user,
                    amount=Decimal(str(random.choice([500, 1000, 2000, 5000, 10000, 20000]))),
                    status=status,
                    reference=f"DEP-{uuid.uuid4().hex[:10].upper()}",
                    payment_type="CREDIT",
                    recieved=status == "SUCCESS",
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f"    ✓ {count} deposits created"))

    # ─────────────────────────────────────────
    # Withdrawals
    # ─────────────────────────────────────────

    def _seed_withdrawals(self, users):
        from payments.models import Withdrawal

        self.stdout.write("  Creating withdrawals...")
        banks = [
            ("Access Bank", "044"), ("GTBank", "058"), ("First Bank", "011"),
            ("UBA", "033"), ("Zenith Bank", "057"), ("Kuda", "090267"),
        ]
        count = 0
        for user in users:
            num = random.randint(0, 3)
            for _ in range(num):
                bank_name, bank_code = random.choice(banks)
                approval = random.choices(["APPROVED", "PENDING", "REJECTED"], weights=[60, 25, 15])[0]
                tx_status = "SUCCESS" if approval == "APPROVED" else "PENDING"
                Withdrawal.objects.create(
                    user=user,
                    amount=Decimal(str(random.choice([500, 1000, 2000, 5000]))),
                    bank_name=bank_name,
                    bank_code=bank_code,
                    account_number=f"{random.randint(10**9, 10**10 - 1)}",
                    account_name=f"{user.first_name} {user.last_name}",
                    status=approval,
                    transaction_status=tx_status,
                    reference=f"WTH-{uuid.uuid4().hex[:10].upper()}",
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f"    ✓ {count} withdrawals created"))

    # ─────────────────────────────────────────
    # Purchases
    # ─────────────────────────────────────────

    def _seed_purchases(self, users):
        from orders.models import Purchase

        self.stdout.write("  Creating purchases...")
        service_templates = [
            ("airtime", 50, 2000, "080"),
            ("data", 99, 5000, "090"),
            ("electricity", 1000, 20000, "METER"),
            ("tv", 2500, 15000, "SMARTCARD"),
            ("internet", 1000, 10000, "ISP"),
            ("education", 500, 5000, "EXAM"),
        ]
        count = 0
        for user in users:
            num = random.randint(2, 10)
            for _ in range(num):
                svc, min_amt, max_amt, prefix = random.choice(service_templates)
                status = random.choices(["success", "pending", "failed"], weights=[75, 15, 10])[0]

                if prefix in ("080", "090"):
                    beneficiary = f"{prefix}{random.randint(10**7, 10**8 - 1)}"
                elif prefix == "METER":
                    beneficiary = f"{random.randint(10**10, 10**11 - 1)}"
                elif prefix == "SMARTCARD":
                    beneficiary = f"{random.randint(10**9, 10**10 - 1)}"
                else:
                    beneficiary = f"{prefix}-{random.randint(1000, 9999)}"

                days_ago = random.randint(0, 60)
                Purchase.objects.create(
                    purchase_type=svc,
                    user=user,
                    reference=f"PUR-{uuid.uuid4().hex[:10].upper()}",
                    amount=Decimal(str(random.randint(min_amt, max_amt))),
                    beneficiary=beneficiary,
                    status=status,
                    remarks=f"Auto-seeded {svc} purchase" if status == "failed" else "",
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f"    ✓ {count} purchases created"))

    # ─────────────────────────────────────────
    # Support Tickets
    # ─────────────────────────────────────────

    def _seed_support_tickets(self, users):
        from support.models import SupportTicket, TicketMessage

        self.stdout.write("  Creating support tickets...")
        subjects = [
            ("Transaction not credited", "transaction"),
            ("Cannot fund my wallet", "wallet"),
            ("My account is locked", "account"),
            ("Data purchase failed but debited", "transaction"),
            ("Wrong electricity token", "transaction"),
            ("How to upgrade to agent?", "other"),
            ("Withdrawal not received", "wallet"),
            ("Virtual account not working", "account"),
        ]
        admin_user = User.objects.filter(is_superuser=True).first()
        count = 0
        msg_count = 0

        for user in random.sample(users, min(len(users), 8)):
            subject, category = random.choice(subjects)
            ticket_status = random.choice(["open", "in_progress", "resolved", "closed"])

            ticket = SupportTicket.objects.create(
                user=user,
                subject=subject,
                description=f"Hello, I am experiencing an issue: {subject}. "
                            f"My phone number is {user.phone_number}. Please help.",
                category=category,
                status=ticket_status,
                related_reference=f"REF-{uuid.uuid4().hex[:8].upper()}" if category == "transaction" else "",
            )
            count += 1

            # Add user message
            TicketMessage.objects.create(
                ticket=ticket, sender=user, is_admin=False,
                message=f"Hi, I need help with: {subject}. It has been affecting my usage."
            )
            msg_count += 1

            # Add admin reply sometimes
            if admin_user and ticket_status in ("in_progress", "resolved", "closed"):
                TicketMessage.objects.create(
                    ticket=ticket, sender=admin_user, is_admin=True,
                    message="Thank you for reaching out. We are looking into this and will update you shortly."
                )
                msg_count += 1

                if ticket_status in ("resolved", "closed"):
                    TicketMessage.objects.create(
                        ticket=ticket, sender=admin_user, is_admin=True,
                        message="This issue has been resolved. Please let us know if you need further assistance."
                    )
                    msg_count += 1

        self.stdout.write(self.style.SUCCESS(f"    ✓ {count} tickets, {msg_count} messages created"))

    # ─────────────────────────────────────────
    # Notifications
    # ─────────────────────────────────────────

    def _seed_notifications(self, users):
        from notifications.models import Notification, UserNotification

        self.stdout.write("  Creating notifications...")
        templates = [
            ("Wallet Funded", "Your wallet has been credited with ₦{amt}.", "fcm"),
            ("Purchase Successful", "Your {svc} purchase of ₦{amt} was successful.", "fcm"),
            ("Withdrawal Approved", "Your withdrawal of ₦{amt} has been approved.", "email"),
            ("New Promotion!", "Get 5% cashback on all data purchases today!", "fcm"),
            ("Security Alert", "A login was detected from a new device.", "sms"),
            ("KYC Approved", "Congratulations! Your identity has been verified.", "email"),
            ("Referral Bonus", "You earned ₦{amt} from a referral!", "fcm"),
            ("Maintenance Notice", "Scheduled maintenance on April 10th, 2:00 AM - 4:00 AM.", "fcm"),
        ]
        notif_count = 0
        user_notif_count = 0

        for title, body_template, channel in templates:
            amt = random.choice([500, 1000, 2000, 5000])
            svc = random.choice(["data", "airtime", "tv", "electricity"])
            body = body_template.format(amt=amt, svc=svc)

            notif = Notification.objects.create(title=title, body=body, channel=channel)
            notif_count += 1

            # Assign to random subset of users
            recipients = random.sample(users, min(len(users), random.randint(3, len(users))))
            for user in recipients:
                is_read = random.choice([True, False, False])
                UserNotification.objects.create(
                    notification=notif,
                    user=user,
                    is_read=is_read,
                    read_at=timezone.now() if is_read else None,
                    status="SENT",
                )
                user_notif_count += 1

        self.stdout.write(self.style.SUCCESS(f"    ✓ {notif_count} notifications, {user_notif_count} user-notifications created"))

    # ─────────────────────────────────────────
    # Announcements
    # ─────────────────────────────────────────

    def _seed_announcements(self):
        from notifications.models import Announcement

        self.stdout.write("  Creating announcements...")
        announcements = [
            {
                "title": "🎉 Welcome to Starboy Global!",
                "body": "We are excited to have you on board. Enjoy seamless VTU services at the best rates in Nigeria.",
                "audience": "all", "is_active": True,
            },
            {
                "title": "🚀 Agent Registration Open",
                "body": "Become an agent today and earn commissions on every transaction. Contact support to get started.",
                "audience": "customers", "is_active": True,
            },
            {
                "title": "📢 New Electricity Payment Feature",
                "body": "You can now pay for electricity (prepaid and postpaid) directly from your wallet.",
                "audience": "all", "is_active": True,
            },
            {
                "title": "⚡ Agent Bonus Week",
                "body": "All agents get double commission this week! Valid Monday to Sunday.",
                "audience": "agents", "is_active": True,
                "starts_at": timezone.now() - timedelta(days=2),
                "expires_at": timezone.now() + timedelta(days=5),
            },
            {
                "title": "🔧 Scheduled Maintenance",
                "body": "We will undergo scheduled maintenance on Saturday 12:00 AM - 2:00 AM. Services may be briefly unavailable.",
                "audience": "all", "is_active": False,
            },
        ]
        for data in announcements:
            Announcement.objects.create(**data)

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(announcements)} announcements created"))

    # ─────────────────────────────────────────
    # Referrals
    # ─────────────────────────────────────────

    def _seed_referrals(self, users):
        from users.models import Referral

        self.stdout.write("  Creating referrals...")
        count = 0
        # Pair up users: first half refers second half
        half = len(users) // 2
        for i in range(half):
            referrer = users[i]
            referred = users[half + i]

            # Skip if relationship already exists
            if Referral.objects.filter(referred=referred).exists():
                continue

            bonus_paid = random.choice([True, False])
            Referral.objects.create(
                referrer=referrer,
                referred=referred,
                bonus_paid=bonus_paid,
                bonus_amount=Decimal(str(random.choice([100, 200, 500]))) if bonus_paid else Decimal("0"),
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f"    ✓ {count} referrals created"))

    # ─────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────

    @staticmethod
    def _unique_phone(existing: set) -> str:
        while True:
            phone = f"80{random.randint(10000000, 99999999)}"
            if phone not in existing:
                return phone
