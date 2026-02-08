from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging

from app.db.supabase import supabase
from app.schemas.superuser import (
    SchoolListItem,
    SchoolListResponse,
    SchoolAnalytics,
    PlatformAnalytics,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _extract_data(resp):
    try:
        # supabase-py may return a dict-like or object with .data
        if resp is None:
            return None
        data = getattr(resp, 'data', None)
        if data is None and isinstance(resp, dict):
            data = resp.get('data')
        return data
    except Exception:
        return None


def require_superuser(user_id: str = Query(...)) -> str:
    try:
        resp = supabase.table('profiles').select('id,role').eq('id', user_id).execute()
        data = _extract_data(resp)
        if not data or len(data) == 0:
            raise HTTPException(status_code=403, detail='User not found or unauthorized')
        profile = data[0]
        if profile.get('role') != 'superuser':
            raise HTTPException(status_code=403, detail='Superuser privileges required')
        return user_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error('Error in require_superuser: %s', str(e))
        raise HTTPException(status_code=500, detail='Authorization failure')


@router.get('/superuser/schools', response_model=SchoolListResponse)
def list_schools(
    status: Optional[str] = Query(None),
  sort_by: Optional[str] = Query('name', pattern='^(name|created_at)$'),
order: Optional[str] = Query('asc', pattern='^(asc|desc)$'),
    _super: str = Depends(require_superuser),
):
    try:
        query = supabase.table('schools').select('*')
        if status:
            query = query.eq('status', status)

        # basic fetch
        resp = query.execute()
        schools = _extract_data(resp) or []

        # map admin ids and batch fetch admin profiles
        admin_ids = list({s.get('admin_id') for s in schools if s.get('admin_id')})
        admins_map = {}
        if admin_ids:
            admin_resp = supabase.table('profiles').select('id,full_name,email').in_('id', admin_ids).execute()
            admin_data = _extract_data(admin_resp) or []
            admins_map = {a.get('id'): a for a in admin_data}

        items = []
        for s in schools:
            created_at = None
            try:
                created_at = datetime.fromisoformat(s.get('created_at')) if s.get('created_at') else None
            except Exception:
                created_at = None

            admin = admins_map.get(s.get('admin_id'))
            items.append(
                SchoolListItem(
                    id=s.get('id'),
                    school_name=s.get('school_name'),
                    status=s.get('status'),
                    created_at=created_at,
                    admin_id=s.get('admin_id'),
                    admin_name=admin.get('full_name') if admin else None,
                    admin_email=admin.get('email') if admin else None,
                )
            )

        # sort
        reverse = order == 'desc'
        if sort_by == 'name':
            items.sort(key=lambda x: (x.school_name or '').lower(), reverse=reverse)
        else:
            items.sort(key=lambda x: x.created_at or datetime.min, reverse=reverse)

        return SchoolListResponse(total_schools=len(items), schools=items)
    except HTTPException:
        raise
    except Exception as e:
        logger.error('Error listing schools: %s', str(e))
        raise HTTPException(status_code=500, detail='Failed to list schools')


@router.get('/superuser/schools/{school_id}/analytics', response_model=SchoolAnalytics)
def school_analytics(school_id: str, _super: str = Depends(require_superuser)):
    try:
        # school info
        school_resp = supabase.table('schools').select('id,school_name').eq('id', school_id).execute()
        school_data = _extract_data(school_resp) or []
        school_name = school_data[0].get('school_name') if school_data else None

        # profiles for the school
        profiles_resp = supabase.table('profiles').select('id,role,last_login').eq('school_id', school_id).execute()
        profiles = _extract_data(profiles_resp) or []

        total_users = len(profiles)
        active_users = 0
        users_by_role = {}
        now = datetime.utcnow()
        thirty_days = now - timedelta(days=30)
        for p in profiles:
            role = p.get('role') or 'unknown'
            users_by_role[role] = users_by_role.get(role, 0) + 1
            last_login = p.get('last_login')
            try:
                if last_login:
                    dt = datetime.fromisoformat(last_login)
                    if dt >= thirty_days:
                        active_users += 1
            except Exception:
                # ignore parse errors
                pass

        # classes
        classes_resp = supabase.table('classes').select('id,updated_at').eq('school_id', school_id).execute()
        classes = _extract_data(classes_resp) or []
        total_classes = len(classes)
        active_classes = 0
        for c in classes:
            try:
                updated = c.get('updated_at')
                if updated:
                    dt = datetime.fromisoformat(updated)
                    if dt >= thirty_days:
                        active_classes += 1
            except Exception:
                pass

        # attendance for classes in this school
        class_ids = [c.get('id') for c in classes if c.get('id')]
        total_attendance_records = 0
        present_count = 0
        recent_attendance_activity = 0
        if class_ids:
            att_resp = supabase.table('attendance').select('id,class_id,date,status').in_('class_id', class_ids).execute()
            atts = _extract_data(att_resp) or []
            total_attendance_records = len(atts)
            seven_days = now - timedelta(days=7)
            for a in atts:
                if a.get('status') and a.get('status').lower() == 'present':
                    present_count += 1
                try:
                    date_val = a.get('date')
                    if date_val:
                        dt = datetime.fromisoformat(date_val)
                        if dt >= seven_days:
                            recent_attendance_activity += 1
                except Exception:
                    pass

        attendance_rate = (present_count / total_attendance_records * 100) if total_attendance_records > 0 else 0.0

        return SchoolAnalytics(
            school_id=school_id,
            school_name=school_name,
            total_users=total_users,
            active_users=active_users,
            users_by_role=users_by_role,
            total_classes=total_classes,
            active_classes=active_classes,
            total_attendance_records=total_attendance_records,
            attendance_rate=attendance_rate,
            recent_attendance_activity=recent_attendance_activity,
            generated_at=now,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error('Error generating school analytics for %s: %s', school_id, str(e))
        raise HTTPException(status_code=500, detail='Failed to generate school analytics')


@router.get('/superuser/analytics/platform', response_model=PlatformAnalytics)
def platform_analytics(_super: str = Depends(require_superuser)):
    try:
        now = datetime.utcnow()
        # schools
        schools_resp = supabase.table('schools').select('id,school_name,status').execute()
        schools = _extract_data(schools_resp) or []
        total_schools = len(schools)
        active_schools = sum(1 for s in schools if s.get('status') == 'active')

        # users
        users_resp = supabase.table('profiles').select('id,role,school_id,last_login').execute()
        users = _extract_data(users_resp) or []
        total_users = len(users)
        thirty_days = now - timedelta(days=30)
        active_users = 0
        users_by_role = {}
        for u in users:
            role = u.get('role') or 'unknown'
            users_by_role[role] = users_by_role.get(role, 0) + 1
            try:
                last_login = u.get('last_login')
                if last_login:
                    dt = datetime.fromisoformat(last_login)
                    if dt >= thirty_days:
                        active_users += 1
            except Exception:
                pass

        # classes
        classes_resp = supabase.table('classes').select('id,updated_at,school_id').execute()
        classes = _extract_data(classes_resp) or []
        total_classes = len(classes)
        active_classes = 0
        for c in classes:
            try:
                updated = c.get('updated_at')
                if updated and datetime.fromisoformat(updated) >= thirty_days:
                    active_classes += 1
            except Exception:
                pass

        # attendance
        att_resp = supabase.table('attendance').select('id,class_id,date,status').execute()
        atts = _extract_data(att_resp) or []
        total_attendance_records = len(atts)
        present_count = 0
        recent_activity = 0
        seven_days = now - timedelta(days=7)
        for a in atts:
            if a.get('status') and a.get('status').lower() == 'present':
                present_count += 1
            try:
                date_val = a.get('date')
                if date_val and datetime.fromisoformat(date_val) >= seven_days:
                    recent_activity += 1
            except Exception:
                pass

        overall_attendance_rate = (present_count / total_attendance_records * 100) if total_attendance_records > 0 else 0.0

        # top schools by users
        users_by_school: Dict[str, int] = {}
        for u in users:
            sid = u.get('school_id')
            if sid:
                users_by_school[sid] = users_by_school.get(sid, 0) + 1

        # get school names map
        school_map = {s.get('id'): s for s in schools}

        top_schools_by_users = sorted(
            [
                {"school_id": sid, "school_name": (school_map.get(sid) or {}).get('school_name'), "users": count}
                for sid, count in users_by_school.items()
            ],
            key=lambda x: x['users'],
            reverse=True,
        )[:10]

        # compute attendance per school
        attendance_by_school: Dict[str, Dict[str, int]] = {}
        # need mapping from class_id to school_id
        class_to_school = {c.get('id'): c.get('school_id') for c in classes if c.get('id')}
        for a in atts:
            cid = a.get('class_id')
            sid = class_to_school.get(cid)
            if not sid:
                continue
            rec = attendance_by_school.setdefault(sid, {'present': 0, 'total': 0})
            rec['total'] += 1
            if a.get('status') and a.get('status').lower() == 'present':
                rec['present'] += 1

        top_schools_by_attendance = []
        for sid, rec in attendance_by_school.items():
            rate = (rec['present'] / rec['total'] * 100) if rec['total'] > 0 else 0.0
            top_schools_by_attendance.append({
                'school_id': sid,
                'school_name': (school_map.get(sid) or {}).get('school_name'),
                'attendance_rate': rate,
                'attendance_records': rec['total'],
            })

        top_schools_by_attendance = sorted(top_schools_by_attendance, key=lambda x: x['attendance_rate'], reverse=True)[:10]

        return PlatformAnalytics(
            total_schools=total_schools,
            active_schools=active_schools,
            total_users=total_users,
            active_users=active_users,
            users_by_role=users_by_role,
            total_classes=total_classes,
            active_classes=active_classes,
            total_attendance_records=total_attendance_records,
            overall_attendance_rate=overall_attendance_rate,
            recent_attendance_activity=recent_activity,
            top_schools_by_users=top_schools_by_users,
            top_schools_by_attendance=top_schools_by_attendance,
            generated_at=now,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error('Error generating platform analytics: %s', str(e))
        raise HTTPException(status_code=500, detail='Failed to generate platform analytics')
