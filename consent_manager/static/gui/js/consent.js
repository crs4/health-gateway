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