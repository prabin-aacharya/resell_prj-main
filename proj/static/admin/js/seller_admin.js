// JavaScript for SellerInfo admin form
(function($) {
    $(document).ready(function() {
        // Get references to form fields
        const lookupField = $('#id_lookup_customer');
        const fullNameField = $('#id_full_name');
        const emailField = $('#id_email');
        const phoneField = $('#id_phone');
        
        // Add event listener for lookup field
        lookupField.on('blur', function() {
            const lookupValue = $(this).val().trim();
            if (lookupValue) {
                // Make AJAX call to lookup customer
                $.ajax({
                    url: '/admin/lookup-customer/',
                    type: 'GET',
                    data: { 'q': lookupValue },
                    dataType: 'json',
                    success: function(data) {
                        if (data.found) {
                            // Populate form fields with customer data
                            fullNameField.val(data.name);
                            emailField.val(data.email);
                            phoneField.val(data.phone);
                            
                            // Show success message
                            alert('Customer found! Form has been populated with their information.');
                        } else {
                            // Show not found message
                            alert('No matching customer found. Please enter customer details manually.');
                        }
                    },
                    error: function() {
                        alert('Error looking up customer. Please enter details manually.');
                    }
                });
            }
        });
        
        // Enhance product selection dropdown with search
        $('#id_product').select2({
            placeholder: 'Select a product or leave blank to create new',
            allowClear: true,
            width: '100%'
        });
    });
})(django.jQuery);
