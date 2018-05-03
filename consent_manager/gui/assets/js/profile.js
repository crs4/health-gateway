import React from "react";

class Profile extends React.Component {
    render() {
        const profiles = JSON.parse(this.props.data.payload);
        return profiles.map((p, i) => {
            return <li key={i}>
                {p.clinical_domain}
            </li>
        });
    }
}

export default Profile;