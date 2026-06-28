import run from '@/data/demo-run.json'
import { Dashboard } from '@/components/dashboard'

export default function BattlefieldPage() {
  return <Dashboard run={run} view="battlefield" />
}

