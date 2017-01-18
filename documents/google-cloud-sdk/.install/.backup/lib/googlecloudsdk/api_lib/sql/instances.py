# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Common utility functions for sql instances."""

import argparse
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions


class _BaseInstances(object):
  """Common utility functions for sql instances."""

  @classmethod
  def _SetBackupConfiguration(cls, sql_messages, settings, args, original):
    """Sets the backup configuration for the instance."""
    # create defines '--backup' while patch defines '--no-backup'
    no_backup = getattr(args, 'no_backup', False) or (
        not getattr(args, 'backup', True))

    if original and (
        any([args.backup_start_time, args.enable_bin_log is not None,
             no_backup])):
      if original.settings.backupConfiguration:
        if isinstance(original.settings.backupConfiguration, list):
          # Only one backup configuration was ever allowed.
          # Field switched from list to single object in v1beta4.
          backup_config = original.settings.backupConfiguration[0]
        else:
          backup_config = original.settings.backupConfiguration
      else:
        backup_config = sql_messages.BackupConfiguration(
            startTime='00:00',
            enabled=False),
    elif not any([args.backup_start_time, args.enable_bin_log is not None,
                  no_backup]):
      return

    if not original:
      backup_config = sql_messages.BackupConfiguration(
          startTime='00:00',
          enabled=False)

    if args.backup_start_time:
      backup_config.startTime = args.backup_start_time
      backup_config.enabled = True
    if no_backup:
      if args.backup_start_time or args.enable_bin_log is not None:
        raise exceptions.ToolException(
            ('Argument --no-backup not allowed with'
             ' --backup-start-time or --enable-bin-log'))
      backup_config.enabled = False

    if args.enable_bin_log is not None:
      backup_config.binaryLogEnabled = args.enable_bin_log

    cls.AddBackupConfigToSettings(settings, backup_config)

  @staticmethod
  def _SetDatabaseFlags(sql_messages, settings, args):
    if args.database_flags:
      settings.databaseFlags = []
      for (name, value) in args.database_flags.items():
        settings.databaseFlags.append(sql_messages.DatabaseFlags(
            name=name,
            value=value))
    elif getattr(args, 'clear_database_flags', False):
      settings.databaseFlags = []

  @staticmethod
  def _SetMaintenanceWindow(sql_messages, settings, args, original):
    """Sets the maintenance window for the instance."""
    channel = getattr(args, 'maintenance_release_channel', None)
    day = getattr(args, 'maintenance_window_day', None)
    hour = getattr(args, 'maintenance_window_hour', None)
    if not any([channel, day, hour]):
      return
    maintenance_window = sql_messages.MaintenanceWindow()

    # If there's no existing maintenance window,
    # both or neither of day and hour must be set.
    if (not original or not original.settings or
        not original.settings.maintenanceWindow):
      if ((day is None and hour is not None) or
          (hour is None and day is not None)):
        raise argparse.ArgumentError(
            None,
            'There is currently no maintenance window on the instance. '
            'To add one, specify values for both day, and hour.')

    if channel:
      # Map UI name to API name.
      names = {'production': 'stable', 'preview': 'canary'}
      maintenance_window.updateTrack = names[channel]
    if day:
      # Map day name to number.
      day_num = arg_parsers.DayOfWeek.DAYS.index(day)
      if day_num == 0:
        day_num = 7
      maintenance_window.day = day_num
    if hour is not None:  # must execute on hour = 0
      maintenance_window.hour = hour
    settings.maintenanceWindow = maintenance_window

  @staticmethod
  def _ConstructSettingsFromArgs(sql_messages, args):
    """Constructs instance settings from the command line arguments.

    Args:
      sql_messages: module, The messages module that should be used.
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A settings object representing the instance settings.

    Raises:
      ToolException: An error other than http error occured while executing the
          command.
    """
    settings = sql_messages.Settings(
        tier=args.tier,
        pricingPlan=args.pricing_plan,
        replicationType=args.replication,
        activationPolicy=args.activation_policy)

    # these args are only present for the patch command
    clear_authorized_networks = getattr(args, 'clear_authorized_networks',
                                        False)
    clear_gae_apps = getattr(args, 'clear_gae_apps', False)

    if args.authorized_gae_apps:
      settings.authorizedGaeApplications = args.authorized_gae_apps
    elif clear_gae_apps:
      settings.authorizedGaeApplications = []

    if any([args.assign_ip is not None, args.require_ssl is not None,
            args.authorized_networks, clear_authorized_networks]):
      settings.ipConfiguration = sql_messages.IpConfiguration()
      if args.assign_ip is not None:
        settings.ipConfiguration.enabled = args.assign_ip

      if args.authorized_networks:
        # AclEntry is only available in the v1beta4 version of the API. If it is
        # present, the API expects an AclEntry for the authorizedNetworks list;
        # otherwise, it expects a string.
        if getattr(sql_messages, 'AclEntry', None) is not None:
          authorized_networks = [sql_messages.AclEntry(value=n) for n in
                                 args.authorized_networks]
        else:
          authorized_networks = args.authorized_networks
        settings.ipConfiguration.authorizedNetworks = authorized_networks
      if clear_authorized_networks:
        # For patch requests, this field needs to be labeled explicitly cleared.
        settings.ipConfiguration.authorizedNetworks = []

      if args.require_ssl is not None:
        settings.ipConfiguration.requireSsl = args.require_ssl

    if any([args.follow_gae_app, args.gce_zone]):
      settings.locationPreference = sql_messages.LocationPreference(
          followGaeApplication=args.follow_gae_app,
          zone=args.gce_zone)

    if getattr(args, 'enable_database_replication', None) is not None:
      settings.databaseReplicationEnabled = args.enable_database_replication

    return settings

  @classmethod
  def ConstructInstanceFromArgs(cls, sql_messages, args,
                                original=None, instance_ref=None):
    """Construct a Cloud SQL instance from command line args.

    Args:
      sql_messages: module, The messages module that should be used.
      args: argparse.Namespace, The CLI arg namespace.
      original: sql_messages.DatabaseInstance, The original instance, if some of
          it might be used to fill fields in the new one.
      instance_ref: reference to DatabaseInstance object, used to fill project
          and instance information.

    Returns:
      sql_messages.DatabaseInstance, The constructed (and possibly partial)
      database instance.

    Raises:
      ToolException: An error other than http error occured while executing the
          command.
    """
    settings = cls._ConstructSettingsFromArgs(sql_messages, args)
    cls._SetBackupConfiguration(sql_messages, settings, args, original)
    cls._SetDatabaseFlags(sql_messages, settings, args)
    cls._SetMaintenanceWindow(sql_messages, settings, args, original)

    on_premises_host_port = getattr(args, 'on_premises_host_port', None)
    if on_premises_host_port:
      if args.require_ssl:
        raise exceptions.ToolException('Argument --on-premises-host-port not '
                                       'allowed with --require_ssl')
      settings.onPremisesConfiguration = sql_messages.OnPremisesConfiguration(
          hostPort=on_premises_host_port)

    storage_size = getattr(args, 'storage_size', None)
    if storage_size:
      settings.dataDiskSizeGb = int(storage_size / (1 << 30))

    # these flags are only present for the create command
    region = getattr(args, 'region', None)
    database_version = getattr(args, 'database_version', None)

    instance_resource = sql_messages.DatabaseInstance(
        region=region,
        databaseVersion=database_version,
        masterInstanceName=getattr(args, 'master_instance_name', None),
        settings=settings)

    if hasattr(args, 'master_instance_name'):
      if args.master_instance_name:
        replication = 'ASYNCHRONOUS'
        activation_policy = 'ALWAYS'
        if hasattr(args, 'replica_type') and args.replica_type == 'FAILOVER':
          instance_resource.replicaConfiguration = (
              sql_messages.ReplicaConfiguration(failoverTarget=True))
      else:
        replication = 'SYNCHRONOUS'
        activation_policy = 'ON_DEMAND'
      if not args.replication:
        instance_resource.settings.replicationType = replication
      if not args.activation_policy:
        instance_resource.settings.activationPolicy = activation_policy

    if instance_ref:
      cls.SetProjectAndInstanceFromRef(instance_resource, instance_ref)

    if hasattr(args, 'storage_type') and args.storage_type:
      instance_resource.settings.dataDiskType = 'PD_' + args.storage_type

    if hasattr(args, 'failover_replica_name') and args.failover_replica_name:
      instance_resource.failoverReplica = (
          sql_messages.DatabaseInstance.FailoverReplicaValue(
              name=args.failover_replica_name))

    if (hasattr(args, 'storage_auto_increase') and
        args.storage_auto_increase is not None):
      instance_resource.settings.storageAutoResize = args.storage_auto_increase

    return instance_resource


class InstancesV1Beta3(_BaseInstances):
  """Common utility functions for sql instances V1Beta3."""

  @staticmethod
  def SetProjectAndInstanceFromRef(instance_resource, instance_ref):
    instance_resource.project = instance_ref.project
    instance_resource.instance = instance_ref.instance

  @staticmethod
  def AddBackupConfigToSettings(settings, backup_config):
    settings.backupConfiguration = [backup_config]


class InstancesV1Beta4(_BaseInstances):
  """Common utility functions for sql instances V1Beta4."""

  @staticmethod
  def SetProjectAndInstanceFromRef(instance_resource, instance_ref):
    instance_resource.project = instance_ref.project
    instance_resource.name = instance_ref.instance

  @staticmethod
  def AddBackupConfigToSettings(settings, backup_config):
    settings.backupConfiguration = backup_config
