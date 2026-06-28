import run from '@/data/demo-run.json'
import { Dashboard } from '@/components/dashboard'

export default function RingsPage() {
  return <Dashboard run={run} view="rings" />
}

