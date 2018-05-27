import sys
import datetime

from client.core.models.file import File


class FileView:

    @staticmethod
    def display(file: File) -> None:
        values_to_display = (FileView.display_name(file.name),
                             FileView.display_size(file.size),
                             FileView.display_connection_speed(file.last_chunk_sent_time, file.current_chunk_size),
                             FileView.display_eta(file.size, file.last_chunk_sent_time, file.chunk_size, file.total_bytes_sent),
                             FileView.display_progress_bar(file.total_bytes_sent, file.size),
                             FileView.display_percentage(file.total_bytes_sent, file.size))

        sys.stdout.write("%s   %s   %s   %s  %s %s" % values_to_display)

    @staticmethod
    def update(file: File):
        sys.stdout.write("\033[F")  # Cursor up one line
        sys.stdout.write("\033[K")  # Clear to the end of line (normally don't need)

        FileView.display(file)

    @staticmethod
    def get_connection_speed(last_chunk_sent_time: datetime.datetime, current_chunk_size: int) -> float:
        if last_chunk_sent_time is None:
            return 0.0

        time_elapsed = datetime.datetime.now() - last_chunk_sent_time

        return current_chunk_size / time_elapsed.total_seconds()

    @staticmethod
    def get_sent_percentage(already_sent_size: int, file_size: int) -> float:
        return already_sent_size / file_size * 100

    @staticmethod
    def display_name(name: str) -> str:
        name_length = len(name)

        if name_length > 20:
            return name[:20] + "..."

        return name

    @staticmethod
    def display_size(size: int) -> str:
        if size < 10**3:
            return "%d B" % size
        elif size < 10**6:
            return "%.2f KB" % round(size/(10**3), 2)
        elif size < 10**9:
            return "%.2f MB" % round(size/(10**6), 2)
        elif size < 10**12:
            return "%.2f GB" % round(size/(10**9), 2)
        else:
            return "%.2f TB" % round(size/(10**12), 2)

    @staticmethod
    def display_connection_speed(last_chunk_sent_time: datetime.datetime, last_chunk_size: int) -> str:
        if last_chunk_sent_time is None:
            return "? KB/s"

        connection_speed = FileView.get_connection_speed(last_chunk_sent_time, last_chunk_size)

        if connection_speed < 10**3:
            return "%.2f B/s" % round(connection_speed, 2)
        elif connection_speed < 10**6:
            return "%.2f KB/s" % round(connection_speed/(10**3), 2)
        elif connection_speed < 10**9:
            return "%.2f MB/s" % round(connection_speed/(10**6), 2)
        else:
            return "%.2f GB/s" % round(connection_speed/(10**9), 2)

    @staticmethod
    def display_eta(size: int,
                    last_chunk_sent_time: datetime.datetime,
                    current_chunk_size: int,
                    already_sent_size: int) -> str:

        estimated_connection_speed = FileView.get_connection_speed(last_chunk_sent_time, current_chunk_size)

        if estimated_connection_speed == 0.0:
            return "Unknown ETA"

        remaining_data_size = size - already_sent_size
        remaining_time_seconds = remaining_data_size / estimated_connection_speed

        return str(datetime.timedelta(seconds=remaining_time_seconds))

    @staticmethod
    def display_progress_bar(already_sent_size: int, file_size: int) -> str:
        percentage = FileView.get_sent_percentage(already_sent_size, file_size)
        progression = int(round(20 * percentage / 100))

        return "[" + "#" * progression + " " * (20 - progression) + "]"

    @staticmethod
    def display_percentage(already_sent_size: int, file_size: int) -> str:
        percentage = int(round(FileView.get_sent_percentage(already_sent_size, file_size)))

        return "{0}%".format(percentage)
