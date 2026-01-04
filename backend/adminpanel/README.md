# ChopHive Custom Admin Panel

A fully custom Django admin panel for ChopHive with role-based access control.

## Features

- **Role-Based Access Control**: Admin, Cafeteria Manager, and Rider roles
- **Responsive Design**: Mobile-first layout with TailwindCSS
- **Multiple Dashboards**: 
  - Admin Dashboard (overview, stats, charts)
  - Cafeteria Manager Dashboard (order management by location)
  - Rider Dashboard (batch-based order delivery)
- **Vendor Management**: Enable/disable vendors, view order counts
- **Profile Management**: Update profile and change password

## Setup

### 1. Create Required Groups

Run the management command to create the required groups:

```bash
python manage.py create_groups
```

This creates:
- `Admin` group
- `CafeteriaManager` group
- `Rider` group

### 2. Assign Roles to Users

1. Log into Django Admin at `/admin/`
2. Go to Users
3. Create or edit a user
4. Assign the user to the appropriate Group (Admin, CafeteriaManager, or Rider)
5. Save

### 3. Access the Custom Admin Panel

- **Admin**: `/admin/dashboard/`
- **Cafeteria Manager**: `/admin/cafeteria-manager/`
- **Rider**: `/admin/rider-dashboard/`
- **Login**: `/admin/login/`

## URL Structure

All admin panel URLs are prefixed with `/admin/`:

- `/admin/login/` - Login page
- `/admin/dashboard/` - Admin dashboard
- `/admin/cafeteria-manager/` - Cafeteria manager dashboard
- `/admin/rider-dashboard/` - Rider dashboard
- `/admin/vendors/` - Vendor management (Admin only)
- `/admin/profile/` - User profile
- `/admin/profile/change-password/` - Change password

## Role-Based Redirects

After login, users are automatically redirected to their appropriate dashboard:
- Admin → `/admin/dashboard/`
- Cafeteria Manager → `/admin/cafeteria-manager/`
- Rider → `/admin/rider-dashboard/`

## Permissions

The system uses Django Groups for role management:
- Users must be assigned to a group to access the admin panel
- Each dashboard checks for the appropriate group membership
- Unauthorized access results in a 403 Permission Denied error

## Django Admin Usage

Django's default admin (`/admin/`) should be used ONLY for:
- Creating users
- Assigning users to groups (roles)
- Activating/deactivating users

All operational tasks should be performed in the custom admin panel.

## File Structure

```
adminpanel/
├── management/
│   └── commands/
│       └── create_groups.py
├── templates/
│   └── adminpanel/
│       ├── base.html
│       ├── login.html
│       ├── partials/
│       │   ├── navbar.html
│       │   └── sidebar.html
│       ├── dashboard/
│       │   └── admin_dashboard.html
│       ├── cafeteria/
│       │   └── cafeteria_dashboard.html
│       ├── rider/
│       │   └── rider_dashboard.html
│       ├── vendors/
│       │   └── vendors_list.html
│       └── profile/
│           ├── profile.html
│           └── change_password.html
├── templatetags/
│   └── adminpanel_permissions.py
├── views/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── cafeteria.py
│   ├── rider.py
│   ├── vendors.py
│   └── profile.py
├── middleware.py
├── permissions.py
├── urls.py
└── README.md
```

## Notes

- The middleware (`RoleBasedRedirectMiddleware`) is optional and can be added to `MIDDLEWARE` in settings.py if you want automatic redirects
- All templates use TailwindCSS via CDN
- Chart.js is used for charts in the admin dashboard
- Font Awesome icons are used throughout

