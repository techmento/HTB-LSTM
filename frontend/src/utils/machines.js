// A batch can have several readings for the same machine (e.g. one per
// hour). Several dashboard sections need "current status per machine," not
// "every row," so this picks the most recent reading for each machine_id —
// by timestamp if the upload had Date+Time columns, otherwise by upload
// order (row_index).
export function getLatestPerMachine(results) {
  const latestByMachine = new Map();

  for (const row of results) {
    const existing = latestByMachine.get(row.machine_id);
    if (!existing) {
      latestByMachine.set(row.machine_id, row);
      continue;
    }

    const isNewer =
      row.timestamp && existing.timestamp
        ? new Date(row.timestamp) >= new Date(existing.timestamp)
        : row.row_index >= existing.row_index;

    if (isNewer) {
      latestByMachine.set(row.machine_id, row);
    }
  }

  return Array.from(latestByMachine.values());
}
