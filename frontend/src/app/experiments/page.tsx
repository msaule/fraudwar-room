import run from '@/data/demo-run.json'
import { Dashboard } from '@/components/dashboard'

export default function ExperimentsPage() {
  return <Dashboard run={run} view="experiments" />
}

