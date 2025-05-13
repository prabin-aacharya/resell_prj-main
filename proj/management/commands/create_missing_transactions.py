import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from proj.models import Product, BikePaymentTransaction

class Command(BaseCommand):
    help = 'Creates missing BikePaymentTransaction records for bikes marked as sold'

    def add_arguments(self, parser):
        parser.add_argument('--user_id', type=int, help='Specific user ID to assign as the buyer')
        parser.add_argument('--username', type=str, help='Username to assign as the buyer')
        parser.add_argument('--all', action='store_true', help='Process all sold bikes')

    def handle(self, *args, **options):
        # Get the user if specified
        user_id = options.get('user_id')
        username = options.get('username')
        process_all = options.get('all', False)
        
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(self.style.SUCCESS(f"Found user: {user.username} (ID: {user.id})"))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with ID {user_id} not found"))
                return
        elif username:
            try:
                user = User.objects.get(username=username)
                self.stdout.write(self.style.SUCCESS(f"Found user: {user.username} (ID: {user.id})"))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with username '{username}' not found"))
                return
        
        if not user and not process_all:
            self.stdout.write(self.style.ERROR("Please specify either --user_id, --username, or --all"))
            return
            
        # Get sold bikes without transactions
        sold_bikes = Product.objects.filter(status='sold')
        self.stdout.write(f"Found {sold_bikes.count()} sold bikes")
        
        # For each sold bike, create a transaction if it doesn't exist
        transactions_created = 0
        for bike in sold_bikes:
            # Check if a transaction already exists for this bike
            existing_transaction = BikePaymentTransaction.objects.filter(product=bike).exists()
            
            if not existing_transaction:
                # If processing all bikes without a specific user, use the first admin user
                buyer = user
                if process_all and not buyer:
                    buyer = User.objects.filter(is_staff=True).first()
                    if not buyer:
                        buyer = User.objects.first()  # Fallback to first user if no admin
                        
                if not buyer:
                    self.stdout.write(self.style.WARNING(f"Skipping bike {bike.id}: {bike.title} - No user specified"))
                    continue
                    
                # Create the transaction
                transaction = BikePaymentTransaction.objects.create(
                    pidx=f"MANUAL-{uuid.uuid4()}",
                    purchase_order_id=f"ORDER-MANUAL-{uuid.uuid4()}",
                    product=bike,
                    buyer=buyer,
                    amount=bike.price,
                    status='Completed',
                    transaction_id=f"TXN-MANUAL-{uuid.uuid4()}",
                    payment_method='Manual'
                )
                
                self.stdout.write(self.style.SUCCESS(
                    f"Created transaction for bike {bike.id}: {bike.title} - Assigned to user: {buyer.username}"
                ))
                transactions_created += 1
            else:
                self.stdout.write(
                    f"Bike {bike.id}: {bike.title} already has a transaction record"
                )
                
        self.stdout.write(self.style.SUCCESS(f"Created {transactions_created} new transaction records")) 