from collections import UserDict
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        # Повертає людино-зрозуміле рядкове представлення значення поля
        # Викликається при print(obj), str(obj) та форматуванні f-рядками
        return str(self.value)


class Name(Field):
    def __init__(self, value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Name must be a non-empty string")
        super().__init__(value.strip())


class Phone(Field):
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Phone must be a string of 10 digits")
        # Строга вимога: РІВНО 10 символів і всі вони цифри — нічого зайвого
        if len(value) != 10 or not value.isdigit():
            raise ValueError("Phone number must contain exactly 10 digits with no extra characters")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value: str):
        try:
            # Перевірка формату та існування дати
            dt = datetime.strptime(value, "%d.%m.%Y")
            # За вимогами ДЗ значення у Field.value має бути РЯДОК у форматі DD.MM.YYYY
            normalized = dt.strftime("%d.%m.%Y")
            super().__init__(normalized)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def to_date_this_year(self, year: int) -> date:
        dt = datetime.strptime(self.value, "%d.%m.%Y")
        return date(year, dt.month, dt.day)


class Record:
    def __init__(self, name: str):
        self.name: Name = Name(name)
        self.phones: List[Phone] = []
        self.birthday: Optional[Birthday] = None

    def add_phone(self, phone: str) -> None:
        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str) -> bool:
        """Видаляє перше входження номера. Повертає True, якщо видалено, інакше False."""
        target = self.find_phone(phone)
        if target is None:
            return False
        self.phones.remove(target)
        return True

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        """Замінює old_phone на new_phone. Підіймає ValueError, якщо старий не знайдено або новий некоректний."""
        # Спочатку валідуємо новий номер (може спричинити ValueError)
        new_p = Phone(new_phone)
        old_p = self.find_phone(old_phone)
        if old_p is None:
            raise ValueError("Old phone number not found")
        old_p.value = new_p.value
        
    def find_phone(self, phone: str) -> Optional[Phone]:
        try:
            phone_normalized = Phone(phone).value
        except ValueError:
            return None
        for p in self.phones:
            if p.value == phone_normalized:
                return p
        return None

    def add_birthday(self, bday: str) -> None:
        if self.birthday is not None:
            # Дозволяємо перезаписати? Умова каже що поле може бути тільки одне – перезапишемо.
            self.birthday = Birthday(bday)
        else:
            self.birthday = Birthday(bday)

    def __str__(self):
        parts = [f"Contact name: {self.name.value}"]
        if self.phones:
            parts.append(f"phones: {'; '.join(p.value for p in self.phones)}")
        if self.birthday:
            parts.append(f"birthday: {self.birthday.value}")
        return ", ".join(parts)


class AddressBook(UserDict):
    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def find(self, name: str) -> Optional[Record]:
        return self.data.get(name)

    def delete(self, name: str) -> bool:
        if name in self.data:
            del self.data[name]
            return True
        return False

    def get_upcoming_birthdays(self) -> List[Dict[str, str]]:
        """
        Повертає список словників з контактами, яких потрібно привітати в найближчі 7 днів (включно з сьогодні).
        Якщо день народження припадає на вихідний (субота/неділя), дата привітання переноситься на найближчий понеділок.
        Формат елементів: {"name": <Ім'я>, "birthday": "DD.MM.YYYY"} — дата ПРИВІТАННЯ (а не реального ДН у вихідний).
        """
        today = date.today()
        end_day = today + timedelta(days=7)

        congratulate: Dict[date, List[str]] = {}

        for record in self.data.values():
            if not record.birthday:
                continue
            # Обчислюємо дату ДН у поточному або наступному році
            bday_this_year = record.birthday.to_date_this_year(today.year)
            if bday_this_year < today:
                bday_this_year = record.birthday.to_date_this_year(today.year + 1)

            # Перевіряємо, чи входить у вікно 7 днів включно
            if today <= bday_this_year <= end_day:
                greet_day = bday_this_year
                # Перенесення на понеділок, якщо вихідний (6=Нд? У Python: Monday=0, Sunday=6)
                # субота=5, неділя=6
                if greet_day.weekday() == 5:  # Saturday
                    greet_day = greet_day + timedelta(days=2)
                elif greet_day.weekday() == 6:  # Sunday
                    greet_day = greet_day + timedelta(days=1)

                congratulate.setdefault(greet_day, []).append(record.name.value)

        results: List[Dict[str, str]] = []
        for d in sorted(congratulate.keys()):
            date_str = d.strftime("%d.%m.%Y")
            for name in sorted(congratulate[d]):
                results.append({"name": name, "birthday": date_str})
        return results

    def __str__(self) -> str:
        if not self.data:
            return "AddressBook is empty"
        return "\n".join(str(record) for record in self.data.values())
