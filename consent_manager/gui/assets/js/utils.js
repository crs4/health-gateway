import moment from "moment";

export const arrayToObject = (array, keyField, update) =>
    array.reduce((obj, item) => {
        if (update) {
            obj[item[keyField]] = Object.assign(item, update);
        }
        else {
            obj[item[keyField]] = item;
        }
        return obj
    }, {});

export function* iterate(obj) {
   for (let key of Object.keys(obj)) {
     yield [key, obj[key]];
   }
}

export function copy(obj) {
    return Object.assign({}, obj);
}

export function getDate(date) {
    return date == null ? null : moment(date);
}

export function getFormattedDate(date) {
    return date == null ? null : moment(date).format('L')
}