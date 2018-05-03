// Copyright (c) 2017-2018 CRS4
//
// Permission is hereby granted, free of charge, to any person obtaining a copy of
// this software and associated documentation files (the "Software"), to deal in
// the Software without restriction, including without limitation the rights to use,
// copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
// and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all copies or
// substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
// INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
// AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
// DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import React from 'react'
import Profile from './profile'

class Consent extends React.Component {
    render() {
        const consents =  this.props.data.slice();
        const rows = consents.map((c, i) => {
            if (c.status === "AC") {
                return (
                    <tr key={i} className="table-light">
                        <td>{c.source.name}</td>
                        <td>{c.destination.name}</td>
                        <td>
                            <Profile data={c.profile}/>
                        </td>
                        <td>
                            <input type="checkbox" name="revoke_list" value="{consent.id}"/>
                        </td>
                    </tr>
                )
            }
        });
        return (
            <table className="table">
                <thead>
                <tr className="table-success">
                    <th scope="col">Source</th>
                    <th scope="col">Destination</th>
                    <th scope="col">Data Sent</th>
                    <th scope="col">Revoke</th>
                </tr>
                </thead>
                <tbody>
                {rows}
                </tbody>
            </table>
        )
    }
}

export default Consent;