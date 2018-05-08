import React from 'react'
import NotificationSystem from 'react-notification-system'

class NotificationManager extends React.Component {

    componentDidMount() {
        this.notificationSystem = this.refs.notificationSystem;
    }

    render() {
        const style = {
            Containers: { // Override the notification item
                DefaultStyle: { // Applied to every notification, regardless of the notification level
                    top: '50px'
                }
            }
        };
        return <NotificationSystem ref="notificationSystem"/>
    }

    success(message) {
        this.notificationSystem.addNotification({
            title: 'Success',
            message: message,
            level: 'success',
            position: 'tc',
            autoDismiss: 3
        })
    }

}

export default NotificationManager;