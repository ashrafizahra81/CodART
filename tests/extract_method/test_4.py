"""
    extracting lines containing access to global variables

    test status: pass
"""

from refactorings.extract_method import extract_method
import os
import errno

def main():
    base_dir = '/mnt/d/Sajad/Uni/Spring00/Compiler/CodART/'
    if not os.path.exists(os.path.dirname(
            base_dir + "tests/extract_method/out/benchmark_projects/ganttproject/biz.ganttproject.core/src/main/java/biz/ganttproject/core/calendar/WeekendCalendarImpl.java")):
        try:
            os.makedirs(os.path.dirname(
                base_dir + "tests/extract_method/out/benchmark_projects/ganttproject/biz.ganttproject.core/src/main/java/biz/ganttproject/core/calendar/WeekendCalendarImpl.java"))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    _conf = {
        'target_file': base_dir + "benchmark_projects/ganttproject/biz.ganttproject.core/src/main/java/biz/ganttproject/core/calendar/WeekendCalendarImpl.java",
        'output_file': base_dir + "tests/extract_method/out/benchmark_projects/ganttproject/biz.ganttproject.core/src/main/java/biz/ganttproject/core/calendar/WeekendCalendarImpl.java",
        'lines': [87,88],
        'new_method_name': 'clearMap',
    }
    extract_method(_conf)


if __name__ == '__main__':
    main()
