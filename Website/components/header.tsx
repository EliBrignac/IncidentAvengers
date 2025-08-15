import { Bot } from "lucide-react"
import { Button } from "@/components/ui/button"

export function Header() {
  return (
    <header className="bg-gray-900 border-b border-gray-800">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-white">
              <Bot className="h-6 w-6" />
            </div>
            <div>
              <h1 className="font-serif text-xl font-bold text-white">AI Agent</h1>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-8">
            <a href="#" className="text-sm font-medium text-gray-300 hover:text-white transition-colors">
              Features
            </a>
            <a href="#" className="text-sm font-medium text-gray-300 hover:text-white transition-colors">
              Resources
            </a>
            <a href="#" className="text-sm font-medium text-gray-300 hover:text-white transition-colors">
              About Us
            </a>
          </nav>

          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              className="border-gray-600 text-gray-300 hover:text-white hover:border-gray-500 bg-transparent"
            >
              Log in
            </Button>
            <Button className="bg-green-500 hover:bg-green-600 text-gray-900 font-semibold">Try AI Agent</Button>
          </div>
        </div>
      </div>
    </header>
  )
}
