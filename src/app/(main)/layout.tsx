import { Header } from "./_components/Header";
import { Sidebar } from "./_components/Sidebar";

export default function MainLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen flex flex-col bg-slate-900">
            <Header />
            <div className="flex flex-1">
                <Sidebar />
                <main className="flex-1 bg-[#ECF0F1] overflow-auto px-16 py-8">
                    {children}
                </main>
            </div>
        </div>
    );
}
