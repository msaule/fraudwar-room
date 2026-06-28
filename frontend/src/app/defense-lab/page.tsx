import run from '@/data/demo-run.json'
import { Dashboard } from '@/components/dashboard'

export default function DefenseLabPage() {
  return <Dashboard run={run} view="defense-lab" />
}

