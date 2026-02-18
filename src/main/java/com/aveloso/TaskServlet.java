package com.aveloso;
import javax.servlet.*;
import javax.servlet.http.*;
import javax.servlet.annotation.*;
import java.io.IOException;

@WebServlet("/add-task")
public class TaskServlet extends HttpServlet {
    private TaskDAO dao = new TaskDAO();

    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        String title = req.getParameter("title");
        String desc = req.getParameter("description");
        String date = req.getParameter("dueDate");
        try {
            dao.addTask(title, desc, date);
            resp.sendRedirect("index.html");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
