#include <iostream>
#include <limits>
#include <string>
#include <vector>


struct Cell {
  std::string name;
  int x;
  int y;
};

struct Net {
  std::string name;
  std::vector<int> cell_ids;
};

int calculateHPWL(const Net &net, const std::vector<Cell> &cells) {
  int xmin = std::numeric_limits<int>::max();
  int xmax = std::numeric_limits<int>::min();

  int ymin = std::numeric_limits<int>::max();
  int ymax = std::numeric_limits<int>::min();

  for (int cell_id : net.cell_ids) {
    const Cell &cell = cells[cell_id];

    if (cell.x < xmin)
      xmin = cell.x;

    if (cell.x > xmax)
      xmax = cell.x;

    if (cell.y < ymin)
      ymin = cell.y;

    if (cell.y > ymax)
      ymax = cell.y;
  }

  return (xmax - xmin) + (ymax - ymin);
}

int main() {
  std::vector<Cell> cells = {{"A", 10, 10}, {"B", 30, 20}, {"C", 50, 15}};

  Net net0 = {"N0", {0, 1, 2}};

  int hpwl = calculateHPWL(net0, cells);

  std::cout << "HPWL = " << hpwl << std::endl;

  return 0;
}