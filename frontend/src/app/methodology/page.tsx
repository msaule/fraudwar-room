import run from '@/data/demo-run.json'
import { Dashboard } from '@/components/dashboard'

export default function MethodologyPage() {
  return <Dashboard run={run} view="methodology" />
}

