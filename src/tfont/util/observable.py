from collections.abc import MutableSequence
from enum import Enum, auto, unique
from tfont.util.event import Event, EventArgs


@unique
class ChangeType(Enum):
    ADD = auto()
    REMOVE = auto()
    REPLACE = auto()


class ChangeEventArgs(EventArgs):
    __slots__ = "_action", "_newItems", "_newStartingIndex", \
                "_oldItems", "_oldStartingIndex"

    def __init__(self, action, oldItems, oldStartingIndex, newItems, newStartingIndex):
        self._action = action
        self._oldItems = oldItems
        self._oldStartingIndex = oldStartingIndex
        self._newItems = newItems
        self._newStartingIndex = newStartingIndex

    @property
    def action(self):
        return self._action

    @property
    def newItems(self):
        return self._newItems

    @property
    def newStartingIndex(self):
        return self._newStartingIndex

    @property
    def oldItems(self):
        return self._oldItems

    @property
    def oldStartingIndex(self):
        return self._oldStartingIndex


class ObservableList(MutableSequence):
    __slots__ = "change_event", "_list"

    def __init__(self, items):
        self._list = items

        self.change_event = Event()

    def __delitem__(self, key):
        list_ = self._list

        item = list_[key]
        del list_[key]

        self.signal_remove(item, key)

    def __getitem__(self, key):
        return self._list[key]

    def __len__(self):
        return len(self._list)

    def __setitem__(self, key, value):
        list_ = self._list

        oldValue = list_[key]
        list_[key] = value

        self.signal_replace(oldValue, value, key)

    def insert(self, index, value):
        self._list.insert(index, value)

        self.signal_add(value, index)

    # other methods

    def __iter__(self):
        return iter(self._list)

    def __repr__(self):
        return repr(self._list)

    def __reversed__(self):
        return reversed(self._list)

    # TODO: add direct extend impl?
    # will need support for ranges in the change_event handler

    #

    def signal_add(self, item, index):
        self.change_event(self, EventArgs(
            ChangeType.ADD,
            (item,),
            index,
            None,
            None,
        ))

    def signal_remove(self, item, index):
        self.change_event(self, EventArgs(
            ChangeType.REMOVE,
            None,
            None,
            (item,),
            index,
        ))

    def signal_replace(self, oldItem, newItem, index):
        self.change_event(self, EventArgs(
            ChangeType.REPLACE,
            (oldItem,),
            index,
            (newItem,),
            index
        ))