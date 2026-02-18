package com.aveloso;

import javax.servlet.*;
import javax.servlet.http.*;
import javax.servlet.annotation.*;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.List;

@WebServlet("/task-servlet") // On utilise un nom plus générique
public class TaskServlet extends HttpServlet {
    private TaskDAO dao = new TaskDAO();

    // 1. RÉCUPÉRER LA LISTE (Utilisé par list.html)
    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        resp.setContentType("application/json");
        resp.setCharacterEncoding("UTF-8");
        
        try {
            List<Task> tasks = dao.getAllTasks(); // Nécessite d'ajouter getAllTasks dans ton TaskDAO
            // Transformation simple en pseudo-JSON pour l'exercice
            PrintWriter out = resp.getWriter();
            out.print("[");
            for (int i = 0; i < tasks.size(); i++) {
                Task t = tasks.get(i);
                out.print(String.format("{\"id\":%d, \"title\":\"%s\", \"description\":\"%s\", \"dueDate\":\"%s\"}", 
                          t.getId(), t.getTitle(), t.getDescription(), t.getDueDate()));
                if (i < tasks.size() - 1) out.print(",");
            }
            out.print("]");
            out.flush();
        } catch (Exception e) {
            e.printStackTrace();
            resp.sendError(500);
        }
    }

    // 2. AJOUTER OU SUPPRIMER UNE TÂCHE
    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        String action = req.getParameter("action"); // On ajoute un paramètre action
        
        try {
            if ("delete".equals(action)) {
                int id = Integer.parseInt(req.getParameter("id"));
                dao.deleteTask(id); // Nécessite d'ajouter deleteTask dans ton TaskDAO
            } else {
                // Logique d'ajout par défaut
                String title = req.getParameter("title");
                String desc = req.getParameter("description");
                String date = req.getParameter("dueDate");
                dao.addTask(title, desc, date);
            }
            resp.sendRedirect("list.html"); // Redirige vers la liste après action
        } catch (Exception e) {
            e.printStackTrace();
            resp.sendRedirect("index.html?error=1");
        }
    }
}
