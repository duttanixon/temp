import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { User } from 'lucide-react'

export function Header() {
  return (
    <header className="bg-[#2C3E50] text-white px-4 py-2 flex items-center justify-between">
      <h1 className="text-lg font-semibold">IoT Edge Device Portal</h1>
      
      <div className="flex items-center gap-4">
        {/* <Button variant="ghost" size="icon" className="text-white hover:bg-slate-700">
          <Bell className="h-5 w-5" />
        </Button>
         */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center gap-2 text-white cursor-pointer">
              <User className="h-5 w-5" />
              <span>Customer Admin ▾</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>Profile</DropdownMenuItem>
            <DropdownMenuItem>Settings</DropdownMenuItem>
            <DropdownMenuItem>Logout</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}