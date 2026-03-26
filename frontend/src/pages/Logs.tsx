import LogViewer from '../components/LogViewer';

export default function Logs() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Logs</h1>
        <p className="text-gray-400">Activity logs from your bot (persisted in database)</p>
      </div>

      <LogViewer maxHeight="calc(100vh - 200px)" showControls={true} />
    </div>
  );
}
