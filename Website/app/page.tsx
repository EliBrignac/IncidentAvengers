import { HeroSection } from "@/components/hero-section"
import { Header } from "@/components/header"

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-900">
      <Header />
      <main>
        <HeroSection />
      </main>
    </div>
  )
}
