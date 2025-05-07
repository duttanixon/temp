import { NextRequest, NextResponse } from "next/server";

export async function GET(_: NextRequest, { params }: { params: { id: string } }) {
  console.log('Fetching customer ID:', params.id);

  const url = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers/${params.id}`;
  console.log('Full URL:', url);

  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${process.env.JWT_TOKEN}`,
      Accept: 'application/json',
    },
  });

  if (!res.ok) {
    const error = await res.text();
    console.error('Backend error:', error);
    return new NextResponse(error, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json(data);
}

export async function PUT(req: NextRequest, { params }: { params: { id: string } }) {
  const body = await req.json()
  const { id } = params

  const url = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers/${id}`

  const res = await fetch(url, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${process.env.JWT_TOKEN}`,
      'Content-Type': 'application/json',
      Accept: 'application/json'
    },
    body: JSON.stringify(body)
  })

  if (!res.ok) {
    const error = await res.text()
    console.error('Backend error:', error)
    return new NextResponse(error, { status: res.status })
  }

  const data = await res.json()
  return NextResponse.json(data)
}