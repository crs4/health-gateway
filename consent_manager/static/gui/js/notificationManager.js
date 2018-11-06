import React from 'react'
import NotificationSystem from 'react-notification-system'

class NotificationManager extends React.Component {

    componentDidMount() {
        this.notificationSystem = this.refs.notificationSystem;
    }

    render() {
        return <NotificationSystem ref="notificationSystem"/>
    }

    success(message, callback) {
        this.notificationSystem.addNotification({
            title: 'Success',
            message: message,
            level: 'success',
            position: 'tc',
            autoDismiss: 2,
            dismissible: true,
            onRemove: callback
        })
    }

    error(message) {
        this.notificationSystem.addNotification({
            title: 'Error',
            message: message,
            level: 'error',
            position: 'tc',
            autoDismiss: 2,
            dismissible: true
        })
    }
}

export default NotificationManager;