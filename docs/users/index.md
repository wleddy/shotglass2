# users package

This is a package designed for use in a shotglass based flask web application. It provides Users and Roles functionality 
as well as a Pref table to hold random preferences.

Besides the database functions described below, the `admin.py` module allows you control access
to the site based on user permissions. [Read more here.](/doct/users/admin.md)

The user package extends the SqliteTable class from [shotglass2.takeabeltof.database](/docs/takeabeltof/database.md)
in the following ways:

---
## class User:

Creates a table to hold user information and implements the following:

---
> #### add_role(*user_id,role_id*): => Nothing

Create a UserRole record with role_id of role_id and user_id of user_id.

---
> #### delete(*rec_id*): => Boolean

Delete the user record with id of rec_id. Returns True if the record existed, else False.

Differs from the default behavior only in that it ensures that inactive User records are included.

The delete cascades through the UserRole table to delete related records.

---
> #### get(*id,**kwargs*): => namedlist or None

Return a single namedlist for the user with this id.

If 'id' is a string, try to find the user by username or email using self.get_by_username_or_email

If include_inactive=True is in kwargs the search will include inactive users else only records for active users are returned.

---
> #### get_by_username_or_email(*nameoremail,**kwargs*): => namedlist or None

Return a single namedlist obj or none based on the username or email

If include_inactive=True is in kwargs the search will include inactive users else only records for active users are returned.

---
> #### get_roles(*userID,**kwargs*): => list(namedlist) or None

Return a list of the role namedlist objects for the user's roles or None if not found
    
---
> #### select(***kwargs*): => list(namedlist) or None

Return a list of namedlist objects or None if no records found with:

* 'where' in kwargs = query where clause string.
* 'order_by' in kwargs = query order by clause string.

If include_inactive=True is in kwargs the search will include inactive users else only records for active users are returned.

---
> #### update_last_access(*user_id,no_commit=False*): => Nothing

Update the 'last_access' field with the current datetime. Default is for record to be committed.

---
> #### clear_roles(*user_id*): => Nothing

Delete all UserRole records associated with the user_id.

---
## class Role

Table to contain information of the roles that may be assigned to users.

---
## class UserRole

An associative table to manage the relationship between User and Role records.

---
## class Pref

A table to store more or less random information about this and that.

* Set user_name to user_name of a User record to limit the pref to that user.
* Set expires to a datetime like value to cause a record to expire after that time.  
  It's the responsibility of the calling program to deal with the datetime returned.

---
> #### get(*name,user_name=None,**kwargs*): => namedlist or None

Return a single namedlist where name == Pref.name.

If a pref record is not found and 'default' is in kwargs create a new record and return the result.  
If 'expires' is in kwargs the expiration datetime will be set.

If the record exists, this function will simply deliver it. The record will not be changed in any way.

---
[Return to Docs](/docs/shotglass2/README.md)

