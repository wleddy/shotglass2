.bail on
alter table role add column locked INTEGER DEFAULT 0;
.bail off
