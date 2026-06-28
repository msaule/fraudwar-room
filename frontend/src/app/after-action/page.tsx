import run from '@/data/demo-run.json'
import { Dashboard } from '@/components/dashboard'

export default function AfterActionPage() {
  return <Dashboard run={run} view="after-action" />
}

