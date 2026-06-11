cols = {

    # admin
    "adm_usr": r"""
    user which is granted admin right (references {\tt usr.usr\_code})
    """,
    "adm_tbl": r"""
    table on which this right admin right is granted (references
    {\tt tbl.tbl\_name})
    """,

    # attr
    "atr_code": r"""
    unique attribute code
    """,
    "atr_desc": r"""
    a description of the attribute
    """,

    # local_auth
    "loc_login": """
    login of the user
    """,
    "loc_usr": r"""
    user which is granted access (references {\tt usr.usr\_code})
    """,
    "loc_enabled": """
    1 if local authentication is enabled for the user, 0 otherwise
    """,
    "loc_password": """
    plain-text password
    """,

    # cas_auth
    "cas_usr": r"""
    user which is granted access (references {\tt usr.usr\_code})
    """,
    "cas_enabled": """
    1 is CAS authentication enabled for the user, 0 otherwise
    """,
    "cas_login": """
    login of the user on the CAS server
    """,

    # grp
    "grp_name": """
    unique group name
    """,
    "grp_parent": r"""
    parent group name (possibly empty, references {\tt grp.grp\_name})
    """,

    # tag
    "tag_name": """
    unique tag name
    """,
    "tag_desc": """
    tag description (possibly empty)
    """,
    "tag_color": r"""
    tag color of the form \verb+#RRGGBB+ (possibly empty)
    """,

    # usr_attr
    "uat_attr": r"""
    attribute (references {\tt attr.atr\_code})
    """,
    "uat_usr": r"""
    user (references {\tt usr.usr\_code})
    """,
    "uat_value": """
    value of the attribute for the user
    """,

    # tbl
    "tbl_name": """
    unique table name
    """,

    # usr
    "usr_code": """
    unique user code
    """,
    "usr_eaddr": """
    unique electronic address
    """,
    "usr_fst_name": """
    first name
    """,
    "usr_name": """
    name
    """,

    # usr_grp
    "ugp_usr": r"""
    user (references {\tt usr.usr\_code})
    """,
    "ugp_grp": r"""
    group (references {\tt grp.grp\_name})
    """,
    "ugp_right": """
    right given to the user on the group: 1 for view (right to view
    MCQ submitted for that group), 2 for submit (right to submit MCQ
    for that group)
    """
}


tbls = {
    "usr": """
    This table defines users.
    """,
    "local_auth": r"""
    This table controls local system authentication. Each row gives
    access to one user. The login used by the user to authenticate is
    her/his code. An empty password prevents the user from logging
    meaning that he/she has to first reset his/her password. If not
    empty, the password is given plain.
    """,
    "cas_auth": """
    This table controls CAS authentication. Each row gives access to
    one user.
    """,
    "tag": """
    This table defines tags that can be associated to MCQ items (e.g.,
    questions).
    """,
    "tbl": """
    This table contains the list of names of tables which can be
    administrated through the web interface, i.e., for which CSV file
    submission is allowed.
    """,
    "admin": """
    This table defines grants administration privileges to users on
    tables.
    """,
    "grp": """
    This table defines user groups.
    """,
    "usr_grp": """
    This table defines group memberships.
    """,
    "attr": """
    This table lists attributes that may be associated to users (e.g.,
    student ID).
    """,
    "usr_attr": """
    This table associates users and attributes.
    """
}
