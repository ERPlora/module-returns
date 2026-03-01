"""AI tools for the Returns module."""
from assistant.tools import AssistantTool, register_tool


@register_tool
class ListReturns(AssistantTool):
    name = "list_returns"
    description = "List product returns with status filter."
    module_id = "returns"
    required_permission = "returns.view_return"
    parameters = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Filter: pending, approved, rejected, completed, cancelled"},
            "limit": {"type": "integer"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from returns.models import Return
        qs = Return.objects.select_related('customer', 'reason').all()
        if args.get('status'):
            qs = qs.filter(status=args['status'])
        limit = args.get('limit', 20)
        return {
            "returns": [
                {
                    "id": str(r.id), "number": r.number, "status": r.status,
                    "customer": r.customer.name if r.customer else None,
                    "reason": r.reason.name if r.reason else None,
                    "total_refund": str(r.total_refund), "refund_method": r.refund_method,
                    "created_at": r.created_at.isoformat(),
                }
                for r in qs.order_by('-created_at')[:limit]
            ]
        }


@register_tool
class ListReturnReasons(AssistantTool):
    name = "list_return_reasons"
    description = "List configured return reasons."
    module_id = "returns"
    required_permission = "returns.view_return"
    parameters = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}

    def execute(self, args, request):
        from returns.models import ReturnReason
        return {
            "reasons": [
                {"id": str(r.id), "name": r.name, "restocks_inventory": r.restocks_inventory, "is_active": r.is_active}
                for r in ReturnReason.objects.filter(is_active=True).order_by('sort_order')
            ]
        }


@register_tool
class CreateReturnReason(AssistantTool):
    name = "create_return_reason"
    description = "Create a return reason (e.g., 'Defectuoso', 'Talla incorrecta')."
    module_id = "returns"
    required_permission = "returns.add_returnreason"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string"}, "description": {"type": "string"},
            "restocks_inventory": {"type": "boolean", "description": "Auto-restock when returned"},
            "requires_note": {"type": "boolean"},
        },
        "required": ["name"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from returns.models import ReturnReason
        r = ReturnReason.objects.create(
            name=args['name'], description=args.get('description', ''),
            restocks_inventory=args.get('restocks_inventory', True),
            requires_note=args.get('requires_note', False),
        )
        return {"id": str(r.id), "name": r.name, "created": True}


@register_tool
class ListStoreCredits(AssistantTool):
    name = "list_store_credits"
    description = "List store credits with optional customer filter."
    module_id = "returns"
    required_permission = "returns.view_return"
    parameters = {
        "type": "object",
        "properties": {
            "customer_id": {"type": "string"},
            "is_active": {"type": "boolean"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from returns.models import StoreCredit
        qs = StoreCredit.objects.all()
        if args.get('customer_id'):
            qs = qs.filter(customer_id=args['customer_id'])
        if 'is_active' in args:
            qs = qs.filter(is_active=args['is_active'])
        return {
            "credits": [
                {
                    "id": str(c.id), "code": c.code, "customer_name": c.customer_name,
                    "original_amount": str(c.original_amount), "current_amount": str(c.current_amount),
                    "is_active": c.is_active,
                }
                for c in qs[:50]
            ]
        }
