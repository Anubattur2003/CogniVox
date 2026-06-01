import yaml
import os
from django.conf import settings


def load_config():
    """Load configuration from config.yaml file"""
    config_path = os.path.join(settings.BASE_DIR, 'config.yaml')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        # Return default configuration if file not found
        return {
            'app': {
                'name': 'CogniVox Agentic',
                'environment': 'development',
                'debug': True,
                'secret_key': 'default-secret-key'
            },
            'database': {
                'url': 'sqlite:///db.sqlite3'
            },
            'server': {
                'host': '0.0.0.0',
                'port': 8000,
                'allowed_hosts': ['*']
            },
            'models': {
                'default_name': 'llama3.2',
                'default_requests': 20
            }
        }
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing config.yaml: {e}")


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Get user agent from request"""
    return request.META.get('HTTP_USER_AGENT', '')


def create_audit_log(user, action, resource_type, resource_id=None, details=None, request=None):
    """Create an audit log entry"""
    from .models import AuditLog
    
    # Map action to action_type choices
    action_type_mapping = {
        'POST /api/auth/login/': 'login',
        'POST /api/auth/logout/': 'logout',
        'POST /api/auth/register/': 'create',
    }
    
    # Extract action type from action string or default to 'api_call'
    action_type = 'api_call'
    for key, value in action_type_mapping.items():
        if key in action:
            action_type = value
            break
    
    audit_data = {
        'user': user if user and user.is_authenticated else None,
        'action_type': action_type,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'description': action,
        'metadata': details or {}
    }
    
    if request:
        audit_data.update({
            'ip_address': get_client_ip(request),
            'user_agent': get_user_agent(request)
        })
    
    return AuditLog.objects.create(**audit_data)


def log_api_usage(request, response, start_time):
    """Log API usage statistics"""
    from .models import APIUsageStats
    from datetime import date
    import time
    
    response_time = time.time() - start_time
    
    # Get or create stats for today
    stats, created = APIUsageStats.objects.get_or_create(
        date=date.today(),
        endpoint=request.path,
        method=request.method,
        defaults={
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0
        }
    )
    
    # Update counters
    stats.total_requests += 1
    if 200 <= response.status_code < 400:
        stats.successful_requests += 1
    else:
        stats.failed_requests += 1
    
    # Update average response time
    if stats.avg_response_time:
        stats.avg_response_time = (stats.avg_response_time + response_time) / 2
    else:
        stats.avg_response_time = response_time
    
    stats.save()




def check_subscription_status(user):
    """Check user's subscription status"""
    if not user.subscription_plan:
        return {
            'is_active': False,
            'plan_name': None,
            'expires_at': None
        }
    
    return {
        'is_active': user.is_subscription_active,
        'plan_name': user.subscription_plan.name,
        'expires_at': user.subscription_end_date
    }


def format_error_response(message, code=None, details=None):
    """Format error response consistently"""
    error_response = {'detail': message}
    
    if code:
        error_response['code'] = code
    
    if details:
        error_response['details'] = details
    
    return error_response


def format_success_response(data=None, message=None):
    """Format success response consistently"""
    response = {}
    
    if message:
        response['message'] = message
    
    if data is not None:
        if isinstance(data, dict):
            response.update(data)
        else:
            response['data'] = data
    
    return response


def paginate_queryset(queryset, request, page_size=20):
    """Paginate queryset with consistent format"""
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    page = request.GET.get('page', 1)
    paginator = Paginator(queryset, page_size)
    
    try:
        paginated_data = paginator.page(page)
    except PageNotAnInteger:
        paginated_data = paginator.page(1)
    except EmptyPage:
        paginated_data = paginator.page(paginator.num_pages)
    
    return {
        'results': paginated_data.object_list,
        'pagination': {
            'current_page': paginated_data.number,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'has_next': paginated_data.has_next(),
            'has_previous': paginated_data.has_previous(),
            'page_size': page_size
        }
    }


def generate_unique_filename(original_filename):
    """Generate unique filename for uploads"""
    import uuid
    from pathlib import Path
    
    file_path = Path(original_filename)
    unique_name = f"{uuid.uuid4().hex}_{file_path.stem}{file_path.suffix}"
    return unique_name


def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    import re
    
    # Remove or replace unsafe characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename.strip('-')


def calculate_file_hash(file_content):
    """Calculate hash of file content"""
    import hashlib
    
    if isinstance(file_content, str):
        file_content = file_content.encode('utf-8')
    
    return hashlib.sha256(file_content).hexdigest()


def is_valid_json(json_string):
    """Check if string is valid JSON"""
    import json
    
    try:
        json.loads(json_string)
        return True
    except (ValueError, TypeError):
        return False


def record_api_usage(request, response, start_time):
    """Record API usage statistics"""
    return log_api_usage(request, response, start_time)


def log_api_call(endpoint, method, user=None, success=True, **kwargs):
    """Log API call with simple parameters for backward compatibility"""
    from .models import APIUsageStats
    from datetime import date
    
    # Get or create stats for today
    stats, created = APIUsageStats.objects.get_or_create(
        date=date.today(),
        endpoint=endpoint,
        method=method,
        defaults={
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0
        }
    )
    
    # Update counters
    stats.total_requests += 1
    if success:
        stats.successful_requests += 1
    else:
        stats.failed_requests += 1
    
    stats.save()
    return stats