import Image from "next/image";
import VendorList from "../components/vendor-list";
import { Suspense } from "react";
import Loading from "./loading";

// TODO: Cache Components adoption. Refactor this route so this opt-out can be removed.
// See: https://nextjs.org/docs/app/guides/migrating-to-cache-components
// export const instant = false;

export default function Home() {
  return (
      <div className="container mx-auto px-4">
        <section aria-label="To Do List">
          <h1>#TODO:</h1>
          <p>This site is in early development and may be unstable. Further implementations and styles based on to-do list may be subject to change.</p>
          <br></br>
          <ul>
            <li>Individual crawl scheduling based on their sitemap data</li>
            <li>Increase performance on crawl engine</li>
            <li>UI/UX Aesthetics</li>
            <li>Security check</li>
          </ul>
        </section>
        <section aria-label="Vendor Information Table">
          <h1 className="text-center">List of Vendor Information</h1>
          <div className="overflow-hidden rounded-lg border border-gray-400">
            <Suspense fallback={<Loading />}>
              <table className="table-auto border-collapse w-full">
                <thead>
                  <tr>
                    <th>Vendor Name</th>
                    <th>Business Info</th>
                    <th>Program Info</th>
                  </tr>
                </thead>
                <tbody>
                  <VendorList />
                </tbody>
              </table>
            </Suspense>
          </div>
        </section>
      </div>
  );
}
