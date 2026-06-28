import run from '@/data/demo-run.json'
import { Dashboard } from '@/components/dashboard'

export default function Home() {
  return <Dashboard run={run} view="command" />
}
