import Link from "next/link";
import { Fragment } from "react";

async function getVendorData() {
    const res = await fetch("http://localhost:8000/api/vendors")
    return res.json()
}

async function getAgeRange(program) {
  let ageRange;
  if (program.age_min === null && program.age_max === null) {
    ageRange = "Any Participant";
  } else if (program.age_min !== null && program.age_max === null) {
    ageRange = `${program.age_min}+`;
  } else if (program.age_min === null && program.age_max !== null) {
    ageRange = `${program.age_max}-`;
  } else {
    ageRange = `${program.age_min} - ${program.age_max}`;
  }
  return ageRange
}

async function formatDuration(totalMinutes) {
  const days = Math.floor(totalMinutes / 1440);
  const hours = Math.floor((totalMinutes % 1440) / 60);
  const minutes = Math.floor(totalMinutes % 60);
  const seconds = Math.round((totalMinutes % 1) * 60);

  return `${days}d ${hours}hr ${minutes}min ${seconds}sec`;
}

export default async function VendorList() {
  let vendorData;
  try {
    vendorData = await getVendorData();
  }
  catch (error) {
    vendorData = null;
  }

  // const [vendor] = await Promise.all([vendorData])

  return (
    vendorData === null ? (
      <tr>
        <td colSpan="3" className="text-center text-red-500">Data Unreachable!</td>
      </tr>
    ) : (
      vendorData.map((vendor) => {
        const mainLocation = vendor.main.location;
        const mainContact = vendor.main.contact;

        const programInfo = vendor.program;
        return (
          <tr key={vendor.id}>
            <td className="text-xl font-bold"><Link href={vendor.domain} target="_blank">{vendor.name}</Link></td>
            <td>
              <span className="font-bold">Has SDP: </span>
              <span className={`${vendor.has_sdp ? "bg-green-500" : "bg-red-500"} px-2 py-1 rounded-full`}>{vendor.has_sdp.toString()}</span>
              <p className="font-bold">Location:</p>
              <div className="space-y-4">
                {mainLocation.map((main) => (
                  <ul key={main.id}>
                    <li>Name: {main.name}</li>
                    <li>Address: {main.street}, {main.city}, {main.state} {main.zipcode}</li>
                  </ul>
                ))}
              </div>
              <p className="font-bold">Contact:</p>
              <div className="space-y-4">
                {mainContact.map((main) => (
                  <ul key={main.id}>
                    <li>Name: {main.name}</li>
                    <li>Email: {main.email.map((email, index) => (
                      <span key={index}>
                        {index > 0 && <span>, </span>}
                        {email}
                      </span>
                    ))}</li>
                    <li>Phone: {main.phone.map((phone, index) => (
                      <span key={index}>
                        {index > 0 && <span>, </span>}
                        {phone}
                      </span>
                    ))}</li>
                  </ul>
                ))}
              </div>
            </td>
            <td key={programInfo.id}>
              {programInfo.map((program) => {
                const ageRange = getAgeRange(program);
                const duration = formatDuration(program.duration);

                const programLocation = program.location;
                const programContact = program.contact;

                return (
                  <div key={program.id}>
                    <h3>{program.name}</h3>
                    <p>Age Range: {ageRange}</p>
                    <p>Price: ${program.amount}</p>
                    <p>Duration: {duration}</p>
                    <p>Location:</p>
                    {programLocation.map((location) => (
                      <ul key={location.id}>
                        <li>Name: {location.name}</li>
                        <li>Address: {location.street}, {location.city}, {location.state}, {location.zipcode}</li>
                      </ul>
                    ))}
                    <p>Contact:</p>
                    <div className="space-y-4">
                      {programContact.map((contact) => (
                        <ul key={contact.id}>
                          <li>Name: {contact.name}</li>
                          <li>Email: {contact.email.map((email) => (
                            email
                          ))}</li>
                          <li>Phone: {contact.phone.map((phone) => (
                            phone
                          ))}</li>
                        </ul>
                      ))}
                    </div>
                  </div>
                )
              })}
            </td>
          </tr>
        )
      })
    )
  )
}