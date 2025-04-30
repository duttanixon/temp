import { NextRequest, NextResponse } from 'next/server'

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const skip = searchParams.get('skip') || '0'
  const limit = searchParams.get('limit') || '100'

  const url = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers?skip=${skip}&limit=${limit}`

  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${process.env.JWT_TOKEN}`,
      Accept: 'application/json'
    }
  })

  const data = await res.json()
  return NextResponse.json(data)
}

export async function POST(req: NextRequest) {
  const body = await req.json()

  const url = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/${process.env.NEXT_PUBLIC_BACKEND_API_VERSION}/customers`

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.JWT_TOKEN}`,
      'Content-Type': 'application/json',
      Accept: 'application/json'
    },
    body: JSON.stringify(body)
  })

  if (!res.ok) {
    const error = await res.text()
    return new NextResponse(error, { status: res.status })
  }

  const data = await res.json()
  return NextResponse.json(data)
}


