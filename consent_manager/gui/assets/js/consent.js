import React from 'react'

class Profile extends React.Component {
    render() {
        const profiles = JSON.parse(this.props.data.payload);
        console.log(this.props.data.payload);
        return <span>{profiles[0].clinical_domain}</span>
    }
}

class Consent extends React.Component {
    render() {
        const consents =  this.props.data.slice();
        console.log(consents);
        const rows = consents.map((consent, index) => {
            if (consent.status === "AC") {
                return (
                    <tr key={index} className="table-light">
                        <td>{consent.source.name}</td>
                        <td>{consent.destination.name}</td>
                        <td>
                            <Profile data={consent.profile}/>
                        </td>
                        <td>
                            <input type="checkbox" name="revoke_list" value="{consent.id}"/>
                        </td>

                    </tr>
                )
            }
        });
        console.log(rows)
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
                {/*{% for consent in consents %}*/}
                {/*{% if forloop.counter0|divisibleby:2 %}*/}
                {/*<tr className="table-light">*/}
                {/*{% else %}*/}
                {/*<tr className="table-light">*/}
                {/*{% endif %}*/}
                {/*<td>{{consent.source_name}}</td>*/}
                {/*<td>{{consent.destination_name}}</td>*/}
                {/*<td>*/}
                {/*{% for record in consent.profile %}*/}
                {/*{{record.clinical_comain}}*/}
                {/*<ul>*/}
                {/*{% for filter in record.filters %}*/}
                {/*{% if filter.includes %}*/}
                {/*<li> {{filter.includes}}</li>*/}
                {/*{% endif %}*/}
                {/*{% endfor %}*/}
                {/*</ul>*/}
                {/*{% endfor %}*/}
                {/*</td>*/}
                {/*{% if status == 0 %}*/}
                {/*<td className="divTableCell">*/}
                {/*<input type="checkbox" name="revoke_list" value="{{ consent.id }}"/>*/}
                {/*</td>*/}
                {/*{% endif %}*/}
                {/*</tr>*/}
                {/*{% endfor %}*/}
                </tbody>
            </table>
        )
    }
}

export default Consent;