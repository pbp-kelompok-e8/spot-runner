from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from .models import Merchandise, Redemption


@admin.register(Merchandise)
class MerchandiseAdmin(admin.ModelAdmin):
    """Merchandise Admin"""
    
    list_display = (
        'image_preview', 
        'name', 
        'category', 
        'price_coins', 
        'stock', 
        'stock_status',
        'organizer_name',
        'total_redeemed',
        'created_at'
    )
    list_filter = ('category', 'created_at', 'organizer')
    search_fields = ('name', 'description', 'organizer__user__username')
    readonly_fields = ('id', 'created_at', 'updated_at', 'image_display', 'redemption_stats')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Product Information', {
            'fields': ('id', 'name', 'description', 'category')
        }),
        ('Pricing & Stock', {
            'fields': ('price_coins', 'stock')
        }),
        ('Organizer', {
            'fields': ('organizer',)
        }),
        ('Image', {
            'fields': ('image_url', 'image_display')
        }),
        ('Statistics', {
            'fields': ('redemption_stats',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        """Show small image preview in list"""
        if obj.image_url:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.image_url
            )
        return '-'
    image_preview.short_description = 'Image'
    
    def image_display(self, obj):
        """Show larger image in detail view"""
        if obj.image_url:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px;" />',
                obj.image_url
            )
        return 'No image'
    image_display.short_description = 'Product Image'
    
    def organizer_name(self, obj):
        """Display organizer name with link"""
        url = f'/admin/event_organizer/eventorganizer/{obj.organizer.user_id}/change/'
        name = obj.organizer.name
        return format_html('<a href="{}">{}</a>', url, name)
    organizer_name.short_description = 'Organizer'
    organizer_name.admin_order_field = 'organizer__user__username'
    
    def stock_status(self, obj):
        """Display stock status with color"""
        if obj.stock == 0:
            color = '#dc2626'  # red
            status = 'Out of Stock'
        elif obj.stock < 10:
            color = '#ea580c'  # orange
            status = 'Low Stock'
        else:
            color = '#16a34a'  # green
            status = 'In Stock'
        
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            color, status
        )
    stock_status.short_description = 'Status'
    
    def total_redeemed(self, obj):
        """Count total redemptions"""
        total = obj.redemptions.aggregate(total=Sum('quantity'))['total'] or 0
        return format_html('<strong>{}</strong> items', total)
    total_redeemed.short_description = 'Redeemed'
    
    def redemption_stats(self, obj):
        """Display detailed redemption statistics"""
        total_redemptions = obj.redemptions.count()
        total_quantity = obj.redemptions.aggregate(total=Sum('quantity'))['total'] or 0
        total_coins = obj.redemptions.aggregate(total=Sum('total_coins'))['total'] or 0
        
        return format_html(
            '<div style="background: #f3f4f6; padding: 12px; border-radius: 6px;">'
            '<strong>Total Redemptions:</strong> {}<br>'
            '<strong>Total Quantity Sold:</strong> {}<br>'
            '<strong>Total Coins Earned:</strong> 🪙 {}<br>'
            '</div>',
            total_redemptions,
            total_quantity,
            total_coins
        )
    redemption_stats.short_description = 'Redemption Statistics'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('organizer__user').prefetch_related('redemptions')
    
    actions = ['mark_out_of_stock', 'add_stock']
    
    def mark_out_of_stock(self, request, queryset):
        """Bulk action to mark as out of stock"""
        updated = queryset.update(stock=0)
        self.message_user(request, f'{updated} product(s) marked as out of stock.')
    mark_out_of_stock.short_description = 'Mark as Out of Stock'
    
    def add_stock(self, request, queryset):
        """Bulk action to add 10 stock to selected items"""
        from django.db.models import F
        updated = queryset.update(stock=F('stock') + 10)
        self.message_user(request, f'Added 10 stock to {updated} product(s).')
    add_stock.short_description = 'Add 10 Stock'


@admin.register(Redemption)
class RedemptionAdmin(admin.ModelAdmin):
    """Redemption Admin"""
    
    list_display = (
        'id_short',
        'get_runner',
        'get_merchandise',
        'quantity',
        'total_coins',
        'redeemed_at'
    )
    list_filter = ('redeemed_at', 'merchandise__category')
    search_fields = (
        'id',
        'user__user__username',
        'user__user__email',
        'merchandise__name'
    )
    readonly_fields = (
        'id',
        'redeemed_at',
        'get_runner_details',
        'get_merchandise_details',
        'transaction_summary'
    )
    date_hierarchy = 'redeemed_at'
    
    fieldsets = (
        ('Redemption Info', {
            'fields': ('id', 'redeemed_at')
        }),
        ('Runner', {
            'fields': ('user', 'get_runner_details')
        }),
        ('Merchandise', {
            'fields': ('merchandise', 'get_merchandise_details')
        }),
        ('Transaction Details', {
            'fields': ('quantity', 'price_per_item', 'total_coins', 'transaction_summary')
        }),
    )
    
    def id_short(self, obj):
        """Display short version of UUID"""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def get_runner(self, obj):
        """Display runner with link"""
        url = f'/admin/main/runner/{obj.user.user_id}/change/'
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.user.user.username
        )
    get_runner.short_description = 'Runner'
    get_runner.admin_order_field = 'user__user__username'
    
    def get_merchandise(self, obj):
        """Display merchandise with link"""
        if obj.merchandise:
            url = f'/admin/merchandise/merchandise/{obj.merchandise.id}/change/'
            return format_html('<a href="{}">{}</a>', url, obj.merchandise.name)
        return format_html('<span style="color: #9ca3af;">[Deleted Product]</span>')
    get_merchandise.short_description = 'Merchandise'
    
    def get_runner_details(self, obj):
        """Display runner details"""
        return format_html(
            '<strong>Username:</strong> {}<br>'
            '<strong>Email:</strong> {}<br>'
            '<strong>Current Coins:</strong> 🪙 {}',
            obj.user.user.username,
            obj.user.user.email,
            obj.user.coin
        )
    get_runner_details.short_description = 'Runner Info'
    
    def get_merchandise_details(self, obj):
        """Display merchandise details"""
        if obj.merchandise:
            return format_html(
                '<strong>Name:</strong> {}<br>'
                '<strong>Category:</strong> {}<br>'
                '<strong>Current Stock:</strong> {}<br>'
                '<strong>Organizer:</strong> {}',
                obj.merchandise.name,
                obj.merchandise.get_category_display(),
                obj.merchandise.stock,
                obj.merchandise.organizer.name
            )
        return 'Product has been deleted'
    get_merchandise_details.short_description = 'Product Info'
    
    def transaction_summary(self, obj):
        """Display transaction summary"""
        return format_html(
            '<div style="background: #f3f4f6; padding: 12px; border-radius: 6px;">'
            '<strong>Quantity:</strong> {} items<br>'
            '<strong>Price per item:</strong> 🪙 {} coins<br>'
            '<strong>Total Cost:</strong> 🪙 <span style="font-size: 18px; font-weight: 700;">{}</span> coins<br>'
            '<hr style="margin: 8px 0; border-color: #d1d5db;">'
            '<strong>Date:</strong> {}'
            '</div>',
            obj.quantity,
            obj.price_per_item,
            obj.total_coins,
            obj.redeemed_at.strftime('%d %B %Y, %H:%M')
        )
    transaction_summary.short_description = 'Transaction Summary'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'user__user',
            'merchandise__organizer__user'
        )
    
    def has_add_permission(self, request):
        """Disable manual redemption creation (should be done via frontend)"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing redemptions"""
        return False


# Optional: Inline for EventOrganizer admin (if you want to show merchandise in organizer admin)
class MerchandiseInline(admin.TabularInline):
    """Inline merchandise for EventOrganizer admin"""
    model = Merchandise
    extra = 0
    fields = ('name', 'category', 'price_coins', 'stock')
    readonly_fields = ('name', 'category', 'price_coins', 'stock')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False