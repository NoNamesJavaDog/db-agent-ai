export function formatDateTime(iso?: string | null): string {
  if (!iso) return '-';
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function truncate(str: string, max = 100): string {
  if (str.length <= max) return str;
  return str.slice(0, max) + '...';
}

export function getDbTypeColor(dbType: string): string {
  const colors: Record<string, string> = {
    postgresql: 'blue',
    mysql: 'orange',
    gaussdb: 'cyan',
    oracle: 'red',
    sqlserver: 'purple',
  };
  return colors[dbType] || 'default';
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    success: 'green',
    completed: 'green',
    error: 'red',
    failed: 'red',
    pending: 'gold',
    executing: 'blue',
    analyzing: 'blue',
    planning: 'cyan',
    skipped: 'default',
  };
  return colors[status] || 'default';
}
