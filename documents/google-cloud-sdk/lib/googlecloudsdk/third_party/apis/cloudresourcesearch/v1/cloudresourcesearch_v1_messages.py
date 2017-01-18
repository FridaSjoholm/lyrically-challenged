"""Generated message classes for cloudresourcesearch version v1.

An API for searching over Google Cloud Platform Resources.
"""
# NOTE: This file is autogenerated and should not be edited by hand.

from apitools.base.protorpclite import messages as _messages
from apitools.base.py import encoding
from apitools.base.py import extra_types


package = 'cloudresourcesearch'


class BillingAccount(_messages.Message):
  """A billing account in [Google Cloud
  Console](https://console.cloud.google.com/). You can assign a billing
  account to one or more projects.

  Fields:
    displayName: The display name given to the billing account, such as `My
      Billing Account`. This name is displayed in the Google Cloud Console.
    name: The resource name of the billing account. The resource name has the
      form `billingAccounts/{billing_account_id}`. For example,
      `billingAccounts/012345-567890-ABCDEF` would be the resource name for
      billing account `012345-567890-ABCDEF`.
    open: True if the billing account is open, and will therefore be charged
      for any usage on associated projects. False if the billing account is
      closed, and therefore projects associated with it will be unable to use
      paid services.
  """

  displayName = _messages.StringField(1)
  name = _messages.StringField(2)
  open = _messages.BooleanField(3)


class CloudresourcesearchResourcesSearchRequest(_messages.Message):
  """A CloudresourcesearchResourcesSearchRequest object.

  Fields:
    orderBy: Comma-separated list of string fields for sorting on the search
      result, including fields from the resources and the built-in fields
      (`resourceName` and `resourceType`). Strings are sorted as binary
      strings based on their UTF-8 encoding.  The default sorting order is
      ascending. To specify descending order for a field, a suffix `" desc"`
      should be appended to the field name. For example: `orderBy="foo
      desc,bar"`.
    pageSize: The maximum number of search results to return per page.
      Searches perform best when the `pageSize` is kept as small as possible.
      If not specified, 20 results are returned per page. At most 1000 results
      are returned per page.
    pageToken: A `nextPageToken` returned from previous SearchResources call
      as the starting point for this call.
    query: The query string in search query syntax. If the query is missing or
      empty, all resources are returned.  Any field in a supported resource
      type's JSON schema may be specified in the query. Additionally, every
      resource has a `@type` field whose value is the resource's type URL. See
      `SearchResult.resource_type` for more information.  Example: The
      following query searches for all Google Compute Engine VM instances
      accessible to the caller. The query is further restricted on the
      `labels` and `machineType` fields of the resource. Only VM instances
      with the label `env` set to "prod" and `machineType` including a token
      phrase with the prefix "n1-stand" are matched.   @type:Instance
      labels.env:prod machineType:n1-stand*
  """

  orderBy = _messages.StringField(1)
  pageSize = _messages.IntegerField(2, variant=_messages.Variant.INT32)
  pageToken = _messages.StringField(3)
  query = _messages.StringField(4)


class Organization(_messages.Message):
  """The root node in the resource hierarchy to which a particular entity's
  (e.g., company) resources belong.

  Enums:
    LifecycleStateValueValuesEnum: The organization's current lifecycle state.
      Assigned by the server. @OutputOnly

  Fields:
    creationTime: Timestamp when the Organization was created. Assigned by the
      server. @OutputOnly
    displayName: A friendly string to be used to refer to the Organization in
      the UI. Assigned by the server, set to the firm name of the Google For
      Work customer that owns this organization. @OutputOnly
    lifecycleState: The organization's current lifecycle state. Assigned by
      the server. @OutputOnly
    name: Output Only. The resource name of the organization. This is the
      organization's relative path in the API. Its format is
      "organizations/[organization_id]". For example, "organizations/1234".
    organizationId: An immutable id for the Organization that is assigned on
      creation. This should be omitted when creating a new Organization. This
      field is read-only. This field is deprecated and will be removed in v1.
      Use name instead.
    owner: The owner of this Organization. The owner should be specified on
      creation. Once set, it cannot be changed. This field is required.
  """

  class LifecycleStateValueValuesEnum(_messages.Enum):
    """The organization's current lifecycle state. Assigned by the server.
    @OutputOnly

    Values:
      LIFECYCLE_STATE_UNSPECIFIED: Unspecified state.  This is only useful for
        distinguishing unset values.
      ACTIVE: The normal and active state.
      DELETE_REQUESTED: The organization has been marked for deletion by the
        user.
    """
    LIFECYCLE_STATE_UNSPECIFIED = 0
    ACTIVE = 1
    DELETE_REQUESTED = 2

  creationTime = _messages.StringField(1)
  displayName = _messages.StringField(2)
  lifecycleState = _messages.EnumField('LifecycleStateValueValuesEnum', 3)
  name = _messages.StringField(4)
  organizationId = _messages.StringField(5)
  owner = _messages.MessageField('OrganizationOwner', 6)


class OrganizationOwner(_messages.Message):
  """The entity that owns an Organization. The lifetime of the Organization
  and all of its descendants are bound to the `OrganizationOwner`. If the
  `OrganizationOwner` is deleted, the Organization and all its descendants
  will be deleted.

  Fields:
    directoryCustomerId: The Google for Work customer id used in the Directory
      API.
  """

  directoryCustomerId = _messages.StringField(1)


class Project(_messages.Message):
  """A Project is a high-level Google Cloud Platform entity.  It is a
  container for ACLs, APIs, AppEngine Apps, VMs, and other Google Cloud
  Platform resources.

  Enums:
    LifecycleStateValueValuesEnum: The Project lifecycle state.  Read-only.

  Messages:
    LabelsValue: The labels associated with this Project.  Label keys must be
      between 1 and 63 characters long and must conform to the following
      regular expression: \[a-z\](\[-a-z0-9\]*\[a-z0-9\])?.  Label values must
      be between 0 and 63 characters long and must conform to the regular
      expression (\[a-z\](\[-a-z0-9\]*\[a-z0-9\])?)?.  No more than 256 labels
      can be associated with a given resource.  Clients should store labels in
      a representation such as JSON that does not depend on specific
      characters being disallowed.  Example: <code>"environment" :
      "dev"</code>  Read-write.

  Fields:
    createTime: Creation time.  Read-only.
    labels: The labels associated with this Project.  Label keys must be
      between 1 and 63 characters long and must conform to the following
      regular expression: \[a-z\](\[-a-z0-9\]*\[a-z0-9\])?.  Label values must
      be between 0 and 63 characters long and must conform to the regular
      expression (\[a-z\](\[-a-z0-9\]*\[a-z0-9\])?)?.  No more than 256 labels
      can be associated with a given resource.  Clients should store labels in
      a representation such as JSON that does not depend on specific
      characters being disallowed.  Example: <code>"environment" :
      "dev"</code>  Read-write.
    lifecycleState: The Project lifecycle state.  Read-only.
    name: The user-assigned display name of the Project. It must be 4 to 30
      characters. Allowed characters are: lowercase and uppercase letters,
      numbers, hyphen, single-quote, double-quote, space, and exclamation
      point.  Example: <code>My Project</code>  Read-write.
    parent: An optional reference to a parent Resource.  The only supported
      parent type is "organization". Once set, the parent cannot be modified.
      Read-write.
    projectId: The unique, user-assigned ID of the Project. It must be 6 to 30
      lowercase letters, digits, or hyphens. It must start with a letter.
      Trailing hyphens are prohibited.  Example: <code>tokyo-rain-123</code>
      Read-only after creation.
    projectNumber: The number uniquely identifying the project.  Example:
      <code>415104041262</code>  Read-only.
  """

  class LifecycleStateValueValuesEnum(_messages.Enum):
    """The Project lifecycle state.  Read-only.

    Values:
      LIFECYCLE_STATE_UNSPECIFIED: Unspecified state.  This is only
        used/useful for distinguishing unset values.
      ACTIVE: The normal and active state.
      DELETE_REQUESTED: The project has been marked for deletion by the user
        (by invoking DeleteProject) or by the system (Google Cloud Platform).
        This can generally be reversed by invoking UndeleteProject.
      DELETE_IN_PROGRESS: This lifecycle state is no longer used and is not
        returned by the API.
    """
    LIFECYCLE_STATE_UNSPECIFIED = 0
    ACTIVE = 1
    DELETE_REQUESTED = 2
    DELETE_IN_PROGRESS = 3

  @encoding.MapUnrecognizedFields('additionalProperties')
  class LabelsValue(_messages.Message):
    """The labels associated with this Project.  Label keys must be between 1
    and 63 characters long and must conform to the following regular
    expression: \[a-z\](\[-a-z0-9\]*\[a-z0-9\])?.  Label values must be
    between 0 and 63 characters long and must conform to the regular
    expression (\[a-z\](\[-a-z0-9\]*\[a-z0-9\])?)?.  No more than 256 labels
    can be associated with a given resource.  Clients should store labels in a
    representation such as JSON that does not depend on specific characters
    being disallowed.  Example: <code>"environment" : "dev"</code>  Read-
    write.

    Messages:
      AdditionalProperty: An additional property for a LabelsValue object.

    Fields:
      additionalProperties: Additional properties of type LabelsValue
    """

    class AdditionalProperty(_messages.Message):
      """An additional property for a LabelsValue object.

      Fields:
        key: Name of the additional property.
        value: A string attribute.
      """

      key = _messages.StringField(1)
      value = _messages.StringField(2)

    additionalProperties = _messages.MessageField('AdditionalProperty', 1, repeated=True)

  createTime = _messages.StringField(1)
  labels = _messages.MessageField('LabelsValue', 2)
  lifecycleState = _messages.EnumField('LifecycleStateValueValuesEnum', 3)
  name = _messages.StringField(4)
  parent = _messages.MessageField('ResourceId', 5)
  projectId = _messages.StringField(6)
  projectNumber = _messages.IntegerField(7)


class ResourceId(_messages.Message):
  """A container to reference an id for any resource type. A `resource` in
  Google Cloud Platform is a generic term for something you (a developer) may
  want to interact with through one of our API's. Some examples are an
  AppEngine app, a Compute Engine instance, a Cloud SQL database, and so on.

  Fields:
    id: Required field for the type-specific id. This should correspond to the
      id used in the type-specific API's.
    type: Required field representing the resource type this id is for. At
      present, the valid types are "project" and "organization".
  """

  id = _messages.StringField(1)
  type = _messages.StringField(2)


class SearchResponse(_messages.Message):
  """Response message for Search().

  Fields:
    matchedCount: The approximate number of documents that match the query. It
      is greater than or equal to the number of documents actually returned.
    nextPageToken: If there are more results, retrieve them by invoking search
      call with the same arguments and this `nextPageToken`. If there are no
      more results, this field is not set.
    results: The list of resources that match the search query.
  """

  matchedCount = _messages.IntegerField(1)
  nextPageToken = _messages.StringField(2)
  results = _messages.MessageField('SearchResult', 3, repeated=True)


class SearchResult(_messages.Message):
  """A single Google Cloud Platform resource returned in
  SearchResourcesResponse.

  Messages:
    ResourceValue: The matched resource, expressed as a JSON object.

  Fields:
    discoveryType: The JSON schema name listed in the discovery document.
      Example: Project
    discoveryUrl: The URL of the discovery document containing the resource's
      JSON schema. Example:
      https://cloudresourcemanager.googleapis.com/$discovery/rest
    resource: The matched resource, expressed as a JSON object.
    resourceName: The RPC resource name. It is a scheme-less URI that includes
      the DNS- compatible API service name. It does not include API version,
      or support %-encoding. Example:
      //cloudresourcemanager.googleapis.com/projects/my-project-123
    resourceType: A domain-scoped name that describes the protocol buffer
      message type. Example:
      type.googleapis.com/google.cloud.resourcemanager.v1.Project
    resourceUrl: The REST URL for accessing the resource. HTTP GET on the
      `resource_url` would return a JSON object equivalent to the `resource`
      below. Example: https://cloudresourcemanager.googleapis.com/v1/projects
      /my-project-123
  """

  @encoding.MapUnrecognizedFields('additionalProperties')
  class ResourceValue(_messages.Message):
    """The matched resource, expressed as a JSON object.

    Messages:
      AdditionalProperty: An additional property for a ResourceValue object.

    Fields:
      additionalProperties: Properties of the object.
    """

    class AdditionalProperty(_messages.Message):
      """An additional property for a ResourceValue object.

      Fields:
        key: Name of the additional property.
        value: A extra_types.JsonValue attribute.
      """

      key = _messages.StringField(1)
      value = _messages.MessageField('extra_types.JsonValue', 2)

    additionalProperties = _messages.MessageField('AdditionalProperty', 1, repeated=True)

  discoveryType = _messages.StringField(1)
  discoveryUrl = _messages.StringField(2)
  resource = _messages.MessageField('ResourceValue', 3)
  resourceName = _messages.StringField(4)
  resourceType = _messages.StringField(5)
  resourceUrl = _messages.StringField(6)


class StandardQueryParameters(_messages.Message):
  """Query parameters accepted by all methods.

  Enums:
    FXgafvValueValuesEnum: V1 error format.
    AltValueValuesEnum: Data format for response.

  Fields:
    f__xgafv: V1 error format.
    access_token: OAuth access token.
    alt: Data format for response.
    bearer_token: OAuth bearer token.
    callback: JSONP
    fields: Selector specifying which fields to include in a partial response.
    key: API key. Your API key identifies your project and provides you with
      API access, quota, and reports. Required unless you provide an OAuth 2.0
      token.
    oauth_token: OAuth 2.0 token for the current user.
    pp: Pretty-print response.
    prettyPrint: Returns response with indentations and line breaks.
    quotaUser: Available to use for quota purposes for server-side
      applications. Can be any arbitrary string assigned to a user, but should
      not exceed 40 characters.
    trace: A tracing token of the form "token:<tokenid>" to include in api
      requests.
    uploadType: Legacy upload protocol for media (e.g. "media", "multipart").
    upload_protocol: Upload protocol for media (e.g. "raw", "multipart").
  """

  class AltValueValuesEnum(_messages.Enum):
    """Data format for response.

    Values:
      json: Responses with Content-Type of application/json
      media: Media download with context-dependent Content-Type
      proto: Responses with Content-Type of application/x-protobuf
    """
    json = 0
    media = 1
    proto = 2

  class FXgafvValueValuesEnum(_messages.Enum):
    """V1 error format.

    Values:
      _1: v1 error format
      _2: v2 error format
    """
    _1 = 0
    _2 = 1

  f__xgafv = _messages.EnumField('FXgafvValueValuesEnum', 1)
  access_token = _messages.StringField(2)
  alt = _messages.EnumField('AltValueValuesEnum', 3, default=u'json')
  bearer_token = _messages.StringField(4)
  callback = _messages.StringField(5)
  fields = _messages.StringField(6)
  key = _messages.StringField(7)
  oauth_token = _messages.StringField(8)
  pp = _messages.BooleanField(9, default=True)
  prettyPrint = _messages.BooleanField(10, default=True)
  quotaUser = _messages.StringField(11)
  trace = _messages.StringField(12)
  uploadType = _messages.StringField(13)
  upload_protocol = _messages.StringField(14)


encoding.AddCustomJsonFieldMapping(
    StandardQueryParameters, 'f__xgafv', '$.xgafv',
    package=u'cloudresourcesearch')
encoding.AddCustomJsonEnumMapping(
    StandardQueryParameters.FXgafvValueValuesEnum, '_1', '1',
    package=u'cloudresourcesearch')
encoding.AddCustomJsonEnumMapping(
    StandardQueryParameters.FXgafvValueValuesEnum, '_2', '2',
    package=u'cloudresourcesearch')
