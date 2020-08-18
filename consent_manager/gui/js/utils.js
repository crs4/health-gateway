/**
 * Create from an array of object a corresponding object where the key is the keyField paramater.
 * It is also possible to add other key => value items using the update paramater
 * @param {!Array} array the array to transform
 * @param {string} keyField the field of the objects to use as the key of the new object
 * @param {Object<string, *>} update an optional object with key => value items to add to the new object
 */
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

/**
 * Iterates over an object
 * @param {Object<string, *>} obj the object to iterate
 */
export function* iterate(obj) {
   for (let key of Object.keys(obj)) {
     yield [key, obj[key]];
   }
}

/**
 * Create a copy of an object
 * @param {*} obj 
 */
export function copy(obj) {
    return Object.assign({}, obj);
}

/**
 * Return a date object or null if the parameter in input is null
 * @param {String} dateISOString
 */
export function getDate(dateISOString) {
    return dateISOString == null ? null : new Date(dateISOString);
}
/**
 * Return a string representation of a date object or null if the parameter in input is null
 * @param {String} dateISOString
 */
export function getFormattedDate(dateISOString) {
    return dateISOString == null ? null : (new Date(dateISOString)).toLocaleDateString('it')
}