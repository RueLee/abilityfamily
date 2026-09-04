import "./globals.css";

export const metadata = {
  title: "Vendor Test List",
  description: "",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`h-full antialiased`}
    >
      <body className="min-h-full flex flex-col items-center">{children}</body>
    </html>
  );
}
